import tinymce from "tinymce";

import "tinymce/icons/default";

import "tinymce/themes/silver";

import "tinymce/plugins/paste";
import "tinymce/plugins/fullscreen";
import "tinymce/plugins/autosave";
import "tinymce/plugins/link";
import "tinymce/plugins/preview";
import "tinymce/plugins/media";
import "tinymce/plugins/image";
import "tinymce/plugins/code";
import "tinymce/plugins/lists";
import "tinymce/plugins/directionality";
import "tinymce/plugins/wordcount";
import "tinymce-i18n/langs/de.js";

import { Editor } from "tinymce";

import { autosaveEditor } from "./autosave";

function parseSvg(svgUrl: string): string {
  return atob(svgUrl.replace("data:image/svg+xml;base64,", ""));
}

/* This function adds an icon which can be inserted in the content */
function addIcon(editor: Editor, tinymceConfig: HTMLElement, name: string): void {
  editor.ui.registry.addIcon(
      name,
      parseSvg(require(`../../svg/${name}.svg`).default)
  );
  editor.ui.registry.addMenuItem(name, {
    text: tinymceConfig.getAttribute(`data-${name}-icon-text`),
    icon: name,
    onAction: () => {
      let src = tinymceConfig.getAttribute(`data-${name}-icon-src`);
      editor.insertContent(`<img src="${src}" style="width:15px; height:15px">`);
    },
  });
}

/* This function toggles the no-translate attribute of a selected text */
function toggleNoTranslate(editor: Editor) {
  editor.focus();
  const val = tinymce.activeEditor.dom.getAttrib(
      tinymce.activeEditor.selection.getNode(),
      "translate",
      "yes"
  );
  if (val == "no") {
    tinymce.activeEditor.dom.setAttrib(
        tinymce.activeEditor.selection.getNode(),
        "translate",
        null
    );
  } else if (editor.selection.getContent().length > 0) {
    editor.selection.setContent(
        '<span class="notranslate" translate="no">' +
        editor.selection.getContent() +
        "</span>"
    );
  }
}

/**
 * This file initializes the tinymce editor.
 */
window.addEventListener("load", () => {
  const tinymceConfig = document.getElementById("tinymce-config-options");

  if (tinymceConfig) {
    tinymce.init({
      selector: ".tinymce_textarea",
      menubar: "edit view insert format icon",
      menu: {
        icon: {
          title: "Icons",
          items: "pin www email call clock idea",
        },
        format: {
          title: "Format",
          items:
            "bold italic underline strikethrough superscript | formats | forecolor backcolor | notranslate",
        },
        insert: {
          title: "Insert",
          items: "openmediacenter add_link link image media "
        }
      },
      link_title: false,
      contextmenu: "paste link",
      autosave_interval: "120s",
      forced_root_block: false,
      plugins:
        "code paste fullscreen autosave link preview media image lists directionality wordcount",
      external_plugins: {
        autolink_tel: tinymceConfig.getAttribute("data-custom-plugins"),
        mediacenter: tinymceConfig.getAttribute("data-custom-plugins"),
        custom_link_input: tinymceConfig.getAttribute("data-custom-plugins"),
      },
      link_default_protocol: "https",
      target_list: false,
      default_link_target: '',
      relative_urls: false,
      remove_script_host: false,
      branding: false,
      toolbar:
        "bold italic underline forecolor | bullist numlist | styleselect | undo redo | ltr rtl notranslate | aligncenter indent outdent | link openmediacenter | export",
      style_formats: [
        {
          title: "Headings",
          items: [
            { title: "Heading 2", format: "h2" },
            { title: "Heading 3", format: "h3" },
            { title: "Heading 4", format: "h4" },
            { title: "Heading 5", format: "h5" },
            { title: "Heading 6", format: "h6" },
          ],
        },
        {
          title: "Inline",
          items: [
            { title: "Bold", format: "bold" },
            { title: "Italic", format: "italic" },
            { title: "Underline", format: "underline" },
            { title: "Strikethrough", format: "strikethrough" },
            { title: "Superscript", format: "superscript" },
            { title: "Subscript", format: "subscript" },
            { title: "Code", format: "code" },
          ],
        },
        {
          title: "Blocks",
          items: [
            { title: "Paragraph", format: "p" },
            { title: "Blockquote", format: "blockquote" },
            { title: "Div", format: "div" },
            { title: "Pre", format: "pre" },
          ],
        },
        {
          title: "Align",
          items: [
            { title: "Left", format: "alignleft" },
            { title: "Center", format: "aligncenter" },
            { title: "Right", format: "alignright" },
            { title: "Justify", format: "alignjustify" },
          ],
        },
      ],
      min_height: 400,
      content_css: tinymceConfig.getAttribute("data-content-css"),
      content_style: tinymceConfig.getAttribute("data-content-style"),
      language: tinymceConfig.getAttribute("data-language"),
      directionality: tinymceConfig.getAttribute("data-directionality") as 'ltr' | 'rtl',
      setup: (editor: Editor) => {
        addIcon(editor, tinymceConfig, "pin");
        addIcon(editor, tinymceConfig, "www");
        addIcon(editor, tinymceConfig, "email");
        addIcon(editor, tinymceConfig, "call");
        addIcon(editor, tinymceConfig, "clock");
        addIcon(editor, tinymceConfig, "idea");
        editor.ui.registry.addIcon(
          "no_translate",
          parseSvg(require("../../svg/no_translate.svg").default)
        );
        editor.ui.registry.addButton("notranslate", {
          tooltip: tinymceConfig.getAttribute("data-no-translate-tooltip"),
          icon: "no_translate",
          onAction: () => toggleNoTranslate(editor),
        });
        editor.ui.registry.addMenuItem("notranslate", {
          text: tinymceConfig.getAttribute("data-no-translate-text"),
          icon: "no_translate",
          onAction: () => toggleNoTranslate(editor),
        });
      },
      readonly: !!tinymceConfig.getAttribute("data-readonly"),
      init_instance_callback: function (editor: Editor) {
        editor.on("StoreDraft", autosaveEditor);
      },
    });
  }
});
