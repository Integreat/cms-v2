import { getCsrfToken } from "../../utils/csrf-token";

(function () {
    'use strict'

    const tinymceConfig = document.getElementById("tinymce-config-options");

    async function getCompletions(query, id) {
        const url = tinymceConfig.getAttribute("data-link-ajax-url");
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCsrfToken(),
            },
            body: JSON.stringify({
                query_string: query
            })
        });
        if (response.status != 200) {
            return [];
        }

        const data = await response.json();
        return [data.data, id];
    }

    // Checks if the url is likely missing the https:// prefix and add it if that is the case
    function checkUrlHttps(url) {
        // This regex matches domains without protocol (strings which contain a dot without a preceding colon or slash)
        const re = new RegExp("^[^:/]+[.].+");
        if (re.test(url)) {
            return "https://" + url;
        }
        return url;
    }

    function updateLink(editor, anchorElm, text, linkAttrs) {
        anchorElm.textContent = text;

        editor.dom.setAttribs(anchorElm, linkAttrs);
        editor.selection.select(anchorElm);
    };


    tinymce.PluginManager.add('custom_link_input', function (editor, _url) {
        function isAnchor(node) {
            return node.nodeName.toLowerCase() === 'a' && node.href;
        }
        function getAnchor() {
            var node = editor.selection.getNode();
            return isAnchor(node) ? node : null;
        };

        const openDialog = function () {
            const initial_text = getAnchor() ? getAnchor().innerText : editor.selection.getContent({ format: "text" });
            const initial_url = editor.selection.getStart().getAttribute("href") || "";

            let prev_search_text = "";
            let prev_link_url = initial_url;
            let prev_selected_completion = "";

            // Store the custom user data separately, so that they can be restored when required
            let user_data = { url: "", text: "" };

            // Stores the current request id, so that outdated requests get ignored
            let ajax_request_id = 0;
            const default_completion_item = { text: "- no results -", value: "" };
            let completion_items = [default_completion_item];
            let current_completion_text = "";

            function updateDialog(api) {
                let data = api.getData();

                let url_changed_by_search = false;
                // Check if the selected completion changed
                if (prev_selected_completion != data.completions) {
                    // find the correct thext currently shown in the completion items box
                    if (completion_items.length > 0) {
                        const current_completion = completion_items.find((completion) => completion.value == data.completions);
                        // Don't set the completion text to `- no results -`
                        if (current_completion.value != "") {
                            current_completion_text = current_completion.text;
                        } else {
                            current_completion_text = "";
                        }
                    } else {
                        current_completion_text = "";
                    }

                    // Set the url either to the selected internal link or to the user link
                    if (data.completions != "") {
                        url_changed_by_search = true;
                        api.setData({ url: data.completions });
                        // if the text is not defined by the user, set it to the current completion item
                        if (!data.text || user_data.text != data.text) {
                            api.setData({ text: current_completion_text });
                        }
                    } else {
                        // restore the original user data
                        api.setData({ url: user_data.url, text: user_data.text });
                    }
                }
                prev_selected_completion = data.completions;

                // Automatically update the text input to the url by default
                data = api.getData();
                if (!url_changed_by_search && data.url != data.text && prev_link_url != data.url && (data.text != user_data.text || !data.text)) {
                    api.setData({ text: data.url });
                }
                prev_link_url = data.url;

                // Update the user link
                if (data.url != data.completions) {
                    user_data.url = data.url;
                }
                if (data.text != data.url && data.text != current_completion_text) {
                    user_data.text = data.text;
                }

                // Disable the submit button if either of url and text are empty
                data = api.getData();
                if (data.url.trim() && data.text.trim()) {
                    api.enable("submit");
                } else {
                    api.disable("submit");
                }

                // make new ajax request on user input
                if (data.search != prev_search_text && data.search != "") {
                    ajax_request_id += 1;
                    getCompletions(data.search, ajax_request_id).then(([new_completions, request_id]) => {
                        if (request_id != ajax_request_id) return;

                        completion_items.length = 0;
                        for (const completion of new_completions) {
                            completion_items.push({
                                text: completion.title,
                                value: completion.url,
                            });
                        }

                        let completions_disabled = false;
                        if (completion_items.length == 0) {
                            completions_disabled = true;
                            completion_items.push(default_completion_item);
                        }

                        // It seems like there is no better way to update the completion list 
                        api.redial(dialog_config);
                        api.setData(data);
                        api.focus("search");
                        prev_search_text = data.search;

                        if (completions_disabled)
                            api.disable("completions");
                        else
                            api.enable("completions");

                        updateDialog(api);
                    });
                } else if (data.search == "" && prev_search_text != "") {
                    // force an update so that the original user url can get restored
                    completion_items.length = 0;
                    completion_items.push(default_completion_item);
                    api.redial(dialog_config);
                    api.setData(data);
                    api.focus("search");
                    prev_search_text = data.search;
                    api.disable("completions");
                    updateDialog(api);
                }
            }

            const dialog_config = {
                title: tinymceConfig.getAttribute("data-link-dialog-title-text"),
                body: {
                    type: "panel",
                    items: [
                        {
                            type: "input",
                            name: "url",
                            label: tinymceConfig.getAttribute("data-link-dialog-url-text")
                        },
                        {
                            type: "input",
                            name: "text",
                            label: tinymceConfig.getAttribute("data-link-dialog-text-text")
                        },
                        {
                            type: "label",
                            label: tinymceConfig.getAttribute("data-link-dialog-internal_link-text"),
                            items: [
                                {
                                    type: "input",
                                    name: "search",
                                },
                                {
                                    type: "selectbox",
                                    name: "completions",
                                    items: completion_items,
                                    disabled: true,
                                }
                            ]
                        }
                    ]
                },
                buttons: [
                    {
                        type: "cancel",
                        text: tinymceConfig.getAttribute("data-dialog-cancel-text")
                    },
                    {
                        type: "submit",
                        name: "submit",
                        text: tinymceConfig.getAttribute("data-dialog-submit-text"),
                        primary: true,
                        disabled: true
                    },
                ],
                initialData: {
                    text: initial_text,
                    url: initial_url,
                },
                onSubmit: function (api) {
                    const data = api.getData();
                    let url = data.url;
                    const text = data.text || url;

                    if (data.url.trim() == "") {
                        return;
                    }
                    api.close();

                    let real_url = checkUrlHttps(url);
                    // Either insert a new link or update the existing one
                    let anchor = getAnchor();
                    if (!anchor) {
                        editor.insertContent(`<a href=${real_url}>${text}</a>`)
                    } else {
                        updateLink(editor, anchor, text, { 'href': real_url });
                    }

                },
                onChange: updateDialog
            };

            return editor.windowManager.open(dialog_config);
        };

        editor.addShortcut("Meta+K", tinymceConfig.getAttribute("data-link-menu-text"), openDialog);

        editor.ui.registry.addMenuItem('add_link', {
            text: tinymceConfig.getAttribute("data-link-menu-text"),
            icon: "link",
            shortcut: "Meta+K",
            onAction: openDialog,
        });

        // This form opens when a link is current selected with the cursor
        editor.ui.registry.addContextForm("link_context_form", {
            predicate: isAnchor,
            initValue: function () {
                var elm = getAnchor();
                return !!elm ? elm.href : '';
            },
            position: "node",
            commands: [
                {
                    type: 'contextformbutton',
                    icon: "link",
                    tooltip: tinymceConfig.getAttribute("data-update-text"),
                    primary: true,
                    onSetup: function (buttonApi) {
                        let nodeChangeHandler = function () {
                            buttonApi.setDisabled(editor.readonly);
                        };
                        editor.on('nodechange', nodeChangeHandler);
                        return function () {
                            editor.off('nodechange', nodeChangeHandler);
                        }
                    },
                    onAction: (formApi) => {
                        const url = formApi.getValue();
                        const real_url = checkUrlHttps(url);
                        const anchor = getAnchor();
                        updateLink(editor, anchor, anchor.innerText, { 'href': real_url });
                        formApi.hide();
                    }
                },
                {
                    type: 'contextformbutton',
                    icon: 'unlink',
                    tooltip: tinymceConfig.getAttribute("data-link-remove-text"),
                    active: false,
                    onAction: (formApi) => {
                        let elm = getAnchor();
                        if (!!elm) {
                            elm.replaceWith(elm.innerHTML)
                        }
                        formApi.hide();
                    }
                },
                {
                    type: 'contextformbutton',
                    icon: 'new-tab',
                    tooltip: tinymceConfig.getAttribute("data-link-open-text"),
                    active: false,
                    onAction: (formApi) => {
                        let elm = getAnchor();
                        if (!!elm) {
                            window.open(elm.getAttribute('href'), '_blank');
                        }
                    }
                }
            ]
        });

        return {};
    })
})();