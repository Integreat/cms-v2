window.addEventListener("load", () => {
    document.querySelectorAll("[data-auto-download]").forEach((node) => {
        setTimeout(function() {
            window.location.href = node.getAttribute('href');
        }, 500);
    });
});
