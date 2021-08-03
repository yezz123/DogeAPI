const faceButton = document.querySelector(".face-button");
const faceContainer = document.querySelector(".face-container");
const containerCoords = document.querySelector("#container");
const mouseCoords = containerCoords.getBoundingClientRect();

faceButton.addEventListener("mousemove", function (e) {
    const mouseX = e.pageX - containerCoords.offsetLeft;
    const mouseY = e.pageY - containerCoords.offsetTop;

    TweenMax.to(faceButton, 0.3, {
        x: ((mouseX - mouseCoords.width / 2) / mouseCoords.width) * 50,
        y: ((mouseY - mouseCoords.height / 2) / mouseCoords.width) * 50,
        ease: Power4.easeOut,
    });
});

faceButton.addEventListener("mousemove", function (e) {
    const mouseX = e.pageX - containerCoords.offsetLeft;
    const mouseY = e.pageY - containerCoords.offsetTop;

    TweenMax.to(faceContainer, 0.3, {
        x: ((mouseX - mouseCoords.width / 2) / mouseCoords.width) * 25,
        y: ((mouseY - mouseCoords.height / 2) / mouseCoords.width) * 25,
        ease: Power4.easeOut,
    });
});

faceButton.addEventListener("mouseenter", function (e) {
    TweenMax.to(faceButton, 0.3, {
        scale: 0.975,
    });
});

faceButton.addEventListener("mouseleave", function (e) {
    TweenMax.to(faceButton, 0.3, {
        x: 0,
        y: 0,
        scale: 1,
    });

    TweenMax.to(faceContainer, 0.3, {
        x: 0,
        y: 0,
        scale: 1,
    });
});
