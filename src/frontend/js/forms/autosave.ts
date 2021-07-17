import { getCsrfToken } from "../utils/csrf-token";
import tinymce from "tinymce";

export async function autosaveEditor() {
  const form = document.getElementById("content_form") as HTMLFormElement;
  tinymce.triggerSave();
  let formData = new FormData(form);
  formData.append("submit_auto", "true");
  const data = await fetch(window.location.href, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: formData
  });
}
