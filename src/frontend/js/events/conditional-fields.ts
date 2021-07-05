/*
 * This file contains functions to show and hide conditional fields
 */

// event handler to show time fields
window.addEventListener("load", () => {
  const isAllDayEl = document.getElementById("id_is_all_day");
  if (isAllDayEl) {
    isAllDayEl.addEventListener("click", ({ target }) => {
      if ((target as HTMLInputElement).checked) {
        document.querySelectorAll(".time-field").forEach((node) => {
          // get plain javascript object of time input field
          const timeInputField = node.querySelector("input");
          // only change behaviour when value is empty
          if (!timeInputField.getAttribute("value")) {
            // remove empty value attribute because it is no valid time value'
            timeInputField.removeAttribute("value");
            // remove required attribute
            timeInputField.removeAttribute("required");
          }
          // hide input field
          node.classList.add("hidden");
        });
      } else {
        document.querySelectorAll(".time-field").forEach((node) => {
          // show input field
          node.classList.remove("hidden");
          // clear value
          node.querySelector("input").value = "";
          // make field required
          node.querySelector("input").required = true;
        });
      }
    });
  }

  // event handler to show recurrence rule form
  const recurrentRuleCheckbox = document.getElementById(
    "recurrence-rule-checkbox"
  );
  if (recurrentRuleCheckbox) {
    recurrentRuleCheckbox.addEventListener("click", ({ target }) => {
      document
        .getElementById("recurrence-rule")
        .classList.toggle("hidden", !(target as HTMLInputElement).checked);
    });
  }
  // event handler to show fields for recurrence frequency
  const frequencyEl = document.getElementById("id_frequency");
  if (frequencyEl) {
    frequencyEl.addEventListener("change", ({ target }) => {
      const recurrenceWeekly = document.getElementById("recurrence-weekly");
      const recurrenceMonthly = document.getElementById("recurrence-monthly");

      recurrenceWeekly.classList.toggle(
        "hidden",
        (target as HTMLInputElement).value !== "WEEKLY"
      );
      recurrenceMonthly.classList.toggle(
        "hidden",
        (target as HTMLInputElement).value !== "MONTHLY"
      );
    });
  }

  // event handler to show recurrence end date
  const recurrenceEndData = document.getElementById(
    "id_has_recurrence_end_date"
  );
  if (recurrenceEndData) {
    recurrenceEndData.addEventListener("click", ({ target }) => {
      const recurrenceEnd = document.getElementById("recurrence-end");
      recurrenceEnd.classList.toggle(
        "hidden",
        !(target as HTMLInputElement).checked
      );
    });
  }

  // event handler to show recurrence rule form
  const locationCheckbox = document.getElementById(
    "id_has_physical_location"
  );
  if (locationCheckbox) {
    locationCheckbox.addEventListener("click", () => {
      document
        .getElementById("location-block")
        .classList.toggle("hidden");
    });
  }
});
