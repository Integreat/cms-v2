/**
 * This file contains all functions which are needed for the diff calculation of revisions.
 */

import HtmlDiff from "htmldiff-js";

window.addEventListener("load", () => {
  // Iterate over revisions and calculate diff
  //setTimeout(function(){
    document.querySelectorAll(".xliff-diff-preview").forEach((xliffImport) => {
    // Calculate the actual diff and insert into the diff div
    xliffImport.querySelector(".xliff-diff-preview-rendered").innerHTML = HtmlDiff.execute(
        xliffImport.querySelector(".xliff-import-source").innerHTML,
        xliffImport.querySelector(".xliff-import-target").innerHTML
      );
  });
  //}, 5000);

  Array.from(document.getElementsByClassName('xliff-show-preview-diff')).forEach((node) => {
    (node as HTMLElement).addEventListener('click', showPreviewDiff);
  });
  Array.from(document.getElementsByClassName('xliff-show-source-code-diff')).forEach((node) => {
    (node as HTMLElement).addEventListener('click', showSourceCodeDiff);
  });
});

function showPreviewDiff({target}: Event) {
  let parent = (target as HTMLElement).closest('ul').parentNode;
  parent.querySelector('.xliff-diff-source-code').classList.add("hidden");
  parent.querySelector('.xliff-diff-preview').classList.remove("hidden");
  let showSourceCodeDiff = parent.querySelector('.xliff-show-source-code-diff');
  showSourceCodeDiff.classList.remove("z-10");
  showSourceCodeDiff.classList.add("cursor-pointer");
  showSourceCodeDiff.firstElementChild.classList.add("hover:bg-blue-500", "hover:text-white");
  let showPreviewDiff = parent.querySelector('.xliff-show-preview-diff');
  showPreviewDiff.firstElementChild.classList.remove("hover:bg-blue-500", "hover:text-white");
  showPreviewDiff.classList.remove("cursor-pointer");
  showPreviewDiff.classList.add("z-10");
}

function showSourceCodeDiff({target}: Event) {
  let parent = (target as HTMLElement).closest('ul').parentNode;
  parent.querySelector('.xliff-diff-preview').classList.add("hidden");
  parent.querySelector('.xliff-diff-source-code').classList.remove("hidden");
  let showPreviewDiff = parent.querySelector('.xliff-show-preview-diff');
  showPreviewDiff.classList.remove("z-10");
  showPreviewDiff.classList.add("cursor-pointer");
  showPreviewDiff.firstElementChild.classList.add("hover:bg-blue-500", "hover:text-white");
  let showSourceCodeDiff = parent.querySelector('.xliff-show-source-code-diff');
  showSourceCodeDiff.firstElementChild.classList.remove("hover:bg-blue-500", "hover:text-white");
  showSourceCodeDiff.classList.remove("cursor-pointer");
  showSourceCodeDiff.classList.add("z-10");
}

