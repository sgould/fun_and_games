(function() {
  // Modified from https://github.com/mdn/samples-server/blob/master/s/webrtc-capturestill
  // by Stephen Gould <stephen.gould@anu.edu.au>

  // The width and height of the captured photo. We will set the
  // width to the value defined here, but the height will be
  // calculated based on the aspect ratio of the input stream.

  var width = 320;    // We will scale the photo width to this
  var height = 0;

  // |streaming| indicates whether or not we're currently streaming
  // video from the camera. Obviously, we start at false.

  var streaming = false;

  // The various HTML elements we need to configure or control. These
  // will be set by the startup() function.

  var video = null;
  var canvas = null;
  var photos = null;

  function startup() {
    video = document.getElementById('video');
    canvas = document.getElementById('canvas');
    photos = new Array();
    photos[0] = document.getElementById('photo1');
    photos[1] = document.getElementById('photo2');
    photos[2] = document.getElementById('photo3');
    photos[3] = document.getElementById('photo4');

    navigator.getMedia = ( navigator.getUserMedia ||
                           navigator.webkitGetUserMedia ||
                           navigator.mozGetUserMedia ||
                           navigator.msGetUserMedia);

    navigator.getMedia(
      {
        video: true,
        audio: false
      },
      function(stream) {
        if (navigator.mozGetUserMedia) {
          video.mozSrcObject = stream;
        } else {
          var vendorURL = window.URL || window.webkitURL;
          video.src = vendorURL.createObjectURL(stream);
        }
        video.play();
      },
      function(err) {
        console.log("An error occured! " + err);
      }
    );

    video.addEventListener('canplay', function(ev) {
      if (!streaming) {
        height = video.videoHeight / (video.videoWidth/width);
      
        // Firefox currently has a bug where the height can't be read from
        // the video, so we will make assumptions if this happens.
      
        if (isNaN(height)) {
          height = width / (4/3);
        }
      
        video.setAttribute('width', width);
        video.setAttribute('height', height);
        canvas.setAttribute('width', width);
        canvas.setAttribute('height', height);
        streaming = true;
      }
    }, false);

    for (var i = 0; i < 4; i++) {
      var callback = (function(i) {
	  return function(ev) {
              //alert("Photo " + i);
              takepicture(i);
              ev.preventDefault();
          }
      })(i);

      photos[i].addEventListener('click', callback, false);
    }

    clearphotos();
  }

  // Fill the photo with an indication that none has been
  // captured.

  function clearphotos() {
    var context = canvas.getContext('2d');
    context.fillStyle = "#AAA";
    context.fillRect(0, 0, canvas.width, canvas.height);

    var data = canvas.toDataURL('image/png');
    for (var i = 0; i < 4; i++) {
      photos[i].setAttribute('src', data);
    }
  }
  
  // Capture a photo by fetching the current contents of the video
  // and drawing it into a canvas, then converting that to a PNG
  // format data URL. By drawing it on an offscreen canvas and then
  // drawing that to the screen, we can change its size and/or apply
  // other changes before drawing it.

  function takepicture(id) {
    var context = canvas.getContext('2d');
    if (width && height) {
      canvas.width = width;
      canvas.height = height;
      context.drawImage(video, 0, 0, width, height);
    
      var data = canvas.toDataURL('image/png');
      photos[id].setAttribute('src', data);
    } else {
      clearphotos();
    }
  }

  // Set up our event listener to run the startup process
  // once loading is complete.
  window.addEventListener('load', startup, false);
})();
