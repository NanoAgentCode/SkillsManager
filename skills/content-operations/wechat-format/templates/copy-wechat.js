async function copyWechatContent(source) {
    const content = source.cloneNode(true);
    for (const image of content.querySelectorAll('img[src]')) {
        image.src = new URL(image.getAttribute('src'), document.baseURI).href;
    }
    const html = content.innerHTML.trim();
    const text = source.innerText.trim();

    // Set the payload explicitly so the browser cannot add preview styles from a selection.
    let payloadSet = false;
    function writeCopyEvent(event) {
        if (!event.clipboardData) return;
        event.clipboardData.setData('text/html', html);
        event.clipboardData.setData('text/plain', text);
        event.preventDefault();
        payloadSet = true;
    }

    document.addEventListener('copy', writeCopyEvent);
    try {
        if (document.execCommand('copy') && payloadSet) return;
    } catch (error) {
        // Some browsers permit only the Clipboard API.
    } finally {
        document.removeEventListener('copy', writeCopyEvent);
    }

    await navigator.clipboard.write([new ClipboardItem({
        'text/html': new Blob([html], { type: 'text/html' }),
        'text/plain': new Blob([text], { type: 'text/plain' }),
    })]);
}
