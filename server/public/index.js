const video = document.getElementById('video');
const video2 = document.getElementById('video2');

const select1 = document.getElementById('devices1');
const select2 = document.getElementById('devices2');

const modes1 = document.getElementById('modes1');
const modes2 = document.getElementById('modes2');

const button1 = document.getElementById('button');
button1.addEventListener('click', () => startDeliveringMedia(select1, video, modes1));

const button2 = document.getElementById('button2');
button2.addEventListener('click', () => startDeliveringMedia(select2, video2, modes2));

let stream;
const connections = [];
let videoDeviceList;

navigator.mediaDevices.enumerateDevices().then(deviceList => {
    videoDeviceList = deviceList.filter(device => device.kind === "videoinput");

    videoDeviceList.forEach(device => {
        const markup = `<option value="${device.deviceId}">${device.label}</option>`;
        select1.innerHTML += markup;
        select2.innerHTML += markup;
    });


});

async function startDeliveringMedia(select, vid, mode){
    const connection = new RTCPeerConnection();
    connections.push(connection);

    connection.addEventListener('track', (event) => mediaReceived(event, vid));
    connection.addEventListener('icecandidate', (event) => iceCandidate(event, mode));

    stream = await navigator.mediaDevices.getUserMedia({ video:
            {
                deviceId: { exact: select.value }
            }
    });

    connection.addTrack(stream.getVideoTracks()[0], stream);

    // create offer:
    const offer = await connection.createOffer();
    await connection.setLocalDescription(offer)
}

async function mediaReceived(event, vid){
    console.log(event);
    vid.srcObject = event.streams[0]
}

async function iceCandidate(event, mode){
    if(!event.candidate){
        console.log("ice gathering finished.");

        const data = {
            mode: mode.value,
            sdp: event.target.localDescription.sdp,
        };

        const response = await fetch('/offer', {
            method: 'POST',
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });


        const answer = await response.json();
        await event.target.setRemoteDescription(answer);
    }
}