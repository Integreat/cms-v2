/*
 * This file contains all functions used for the XLIFF import
 */

// Set event handler
window.addEventListener("load", () => {
    // Event handler for changing the parent page option
    document.getElementById("xliff_file")?.addEventListener("change", selectXliffFile);
});

/**
 * Listen for user input (selection in file browser) for uploading XLIFF files.
 * Updates the UI for submitting.
 *
 * @param {target} eventTarget - The changed file input
 */
function selectXliffFile({ target }: Event) {
    let files = (target as HTMLInputElement).files;
    // Update xliff file label
    let label = document.querySelector("#xliff_file_label");
    label.classList.remove("bg-blue-500", "hover:bg-blue-600");
    label.classList.add("bg-gray-500", "hover:bg-gray-600");
    label.textContent = files[0].name
    if (files.length > 1) {
        // Get translated text for "and {} other files"
        let label_multiple = document.querySelector("#xliff_file_label_multiple");
        label.textContent += label_multiple.textContent.replace("{}", (files.length - 1).toString());
    }
    // Update xliff file submit button
    let submit_button = document.querySelector("#xliff_file_submit") as HTMLInputElement;
    submit_button.classList.remove("cursor-not-allowed", "bg-gray-500");
    submit_button.classList.add("cursor-pointer", "bg-blue-500", "hover:bg-blue-600");
    submit_button.disabled = false;
}
