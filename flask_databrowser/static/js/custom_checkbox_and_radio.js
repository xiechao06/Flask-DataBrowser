// Custom checkbox and radios
var checkBoxInput = "input[type='checkbox']";
var checkBoxSelectedClass = "fa-check-square-o";
var checkBoxUnSelectedClass = "fa-square-o";

var radioInput = "input[type='radio']";
var radioSelectedClass = "fa-check-circle";
var radioUnSelectedClass = "fa-circle-o";

var parentSelectedClass = "active";

var selectedSymbol = ":checked";
var disabledSymbol = ":disabled";
var disabledClass = "disabled";

function toggleAllItem() {
    $(checkBoxInput + ", " + radioInput).each(function (idx, item) {
        toggle(item);
    })
}

function toggleAllRadio() {
    $(radioInput).each(function (idx, item) {
        toggle(item);
    });
}

function toggle(item) {
    var target = $(item).prev("i");
    var selectedClass = $(item).is(checkBoxInput) ? checkBoxSelectedClass : radioSelectedClass;
    var unSelectedClass = $(item).is(checkBoxInput) ? checkBoxUnSelectedClass : radioUnSelectedClass;
    toggleSelected(item, target, selectedClass, unSelectedClass);
}


function toggleAllCheckbox() {
    $(checkBoxInput).each(function (idx, item) {
        toggle(item);
    });
}
function toggleParent(item) {
    var parent = getParentDom(item);
    if ($(item).is(selectedSymbol)) {
        $(parent).addClass(parentSelectedClass);
    } else {
        $(parent).removeClass(parentSelectedClass);
    }
}

function toggleSelected(source, target, selectedClass, unselectedClass) {
    toggleParent(source);
    if ($(source).is(selectedSymbol)) {
        $(target).removeClass(unselectedClass).addClass(selectedClass);
    } else {
        $(target).removeClass(selectedClass).addClass(unselectedClass);
    }
    if ($(source).is(disabledSymbol)) {
        $(target).addClass(disabledClass);
    } else {
        $(target).removeClass(disabledClass);
    }
}

function getIcon(item) {
    var icon = $("<i></i>").addClass("fa").addClass("fa-fw");
    if ($(item).is(checkBoxInput)) {
        icon.addClass("i-checkbox ");
    }
    if ($(item).is(radioInput)) {
        icon.addClass("i-radio ");
    }
    if ($(item).is(disabledSymbol)) {
        icon.addClass(disabledClass);
    }
    icon.addClass(getParentDom(item).length == 0 ? " fa-2x" : " fa-lg");
    return icon;
}

function getParentDom(item) {
    return $(item).parent().not("div");
}

function selectInput(i_item) {
    var input = $(i_item).next("input");
    input.prop("checked", !input.is(selectedSymbol)).trigger("select");
    toggle(input);
}

$(document).ready(function () {
    // First let's prepend icons (needed for effects)
    $(checkBoxInput + ", " + radioInput).each(function (idx, item) {
        $(item).before(getIcon(item));
        $(item).hide();
        toggle(item);
    }).change(function () {
            toggle(this);
        });

    $(".i-checkbox").click(function (e) {
        e.preventDefault();
        if ($(this).hasClass(disabledClass) || $(this).is(disabledSymbol)) {
            return false;
        }
        selectInput(this);
        return false;
    });

    $(".i-radio").click(function (e) {
        e.preventDefault();
        if ($(this).hasClass(disabledClass) || $(this).is(disabledSymbol)) {
            return false;
        }
        selectInput(this);
        toggleAllRadio();
        return false;
    });
});

