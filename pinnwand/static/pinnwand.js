let indents = {
    "python": " ".repeat(4),
    "python2": " ".repeat(4),
};

window.addEventListener("load", (event) => {
    setupColorScheme();

    if(document.querySelector("section.paste-submit")) {
        setupCreatePage();
    } else {
        setupShowPage();
    }
});

function add_new_file() {
    let template = document.querySelector("section.file-template").cloneNode(true);
    template.className = "file-part file-extra";
    template.querySelector("button.remove").addEventListener("click", (event) => {
        event.preventDefault();

        let section = event.target.parentNode.parentNode;

        document.querySelector("main.page-create").removeChild(section);
    });

    template.querySelector("textarea").addEventListener("keydown", indent_textarea);

    document.querySelector("main.page-create").insertBefore(
        template,
        document.querySelector("section.paste-submit")
    );
}


function indent_textarea(event) {
	let selector = event.target.parentNode.parentNode.querySelector("select[name='lexer']"),
	    lexer = selector.options[selector.selectedIndex].text

	if(!(lexer && lexer.toLowerCase().indexOf("python") == 0)) {
		return
	}

    let indent = " ".repeat(4);
	let keyCode = event.keyCode || event.which;

	if (keyCode == 9) {
		event.preventDefault();
		var start = this.selectionStart;
        var end = this.selectionEnd;
		var v = this.value;
		if (start == end) {
		    this.value = v.slice(0, start) + indent + v.slice(start);
		    this.selectionStart = start + indent.length;
		    this.selectionEnd = start + indent.length;
		    return;
		}

		var selectedLines = [];
		var inSelection = false;
		var lineNumber = 0;
		for (var i = 0; i < v.length; i++) {
		    if (i == start) {
                inSelection = true;
                selectedLines.push(lineNumber);
		    }
		    if (i >= end)
                inSelection = false;

		    if (v[i] == "\n") {
			lineNumber++;
			if (inSelection)
			    selectedLines.push(lineNumber);
		    }
		}
		var lines = v.split("\n");
		for (var i = 0; i < selectedLines.length; i++)
		{
		    lines[selectedLines[i]] = indent + lines[selectedLines[i]];
		}

		this.value = lines.join("\n");

		}
	else if (keyCode == 13) {
		event.preventDefault();

		var start = this.selectionStart;
		var end = this.selectionEnd;
        var v = this.value;
        var thisLine = "";
        var indentation = 1;
        for (var i = start-1; i >= 0 && v[i] != "\n"; i--) {
            thisLine = v[i] + thisLine;
        }
        for (var i = 0; i < thisLine.length && thisLine[i] == " "; i++) {
            indentation++;
        }
        this.value = v.slice(0, start) + "\n" + " ".repeat(indentation-1) + v.slice(start);
        this.selectionStart = start + indentation;
        this.selectionEnd = end + indentation;

	}
}

function setupColorScheme() {
    let storage = window.localStorage,
        colorSchemeButton = document.getElementById("toggle-color-scheme");

    if(storage.getItem("other-color") == "true") {
        document.querySelector("html").classList.toggle("other-color");
    }

    if(colorSchemeButton != null) {
        colorSchemeButton.addEventListener("click", function(event) {
            if(storage.getItem("other-color") == "true") {
                storage.setItem("other-color", "false");
            } else {
                storage.setItem("other-color", "true");
            }

            document.querySelector("html").classList.toggle("other-color");
        });
    }
}

function setupShowPage() {
    let wordWrapButton = document.getElementById("toggle-word-wrap");
    if(wordWrapButton != null) {
        wordWrapButton.addEventListener("click", function(event) {
            let codeBlocks = document.querySelectorAll("div.code");
            for(let i = 0; i < codeBlocks.length; i++) {
                codeBlocks[i].classList.toggle("no-word-wrap");
            }
        });
    }

    let copyButtons = document.querySelectorAll("button.copy-button");

    for(let i = 0; i < copyButtons.length; i++) {
        let copyButton = copyButtons[i];

        copyButton.addEventListener("click", function(event) {
            event.preventDefault();

            let textarea = event.target.parentNode.parentNode.querySelector("textarea.copy-area");
            let listener = (event) => {
                event.preventDefault();
                event.clipboardData.setData("text/plain", textarea.value);
            };

            document.addEventListener('copy', listener);
            document.execCommand('copy');
            document.removeEventListener('copy', listener);
        });
    };

    return false;
}

function setupCreatePage() {
    let removes = document.querySelectorAll("button.remove"),
        bar = document.querySelector("section.paste-submit");

    for(let i = 0; i < removes.length; i++) {
        let remove = removes[i];

        remove.addEventListener("click", (event) => {
            event.preventDefault();

            let section = event.target.parentNode.parentNode;

            document.querySelector("main.page-create").removeChild(section);
        });
    };

    let but = document.createElement("button");

    but.innerText = "Add another file.";
    but.className = "add";
    but.href = "#";

    but.addEventListener("click", function(event) {
        event.preventDefault();

        add_new_file();
    })

    bar.appendChild(but);

    let textareas = document.querySelectorAll('section.file-part textarea');
    for(let i = 0; i < textareas.length; i++) {
        textareas[i].addEventListener("keydown", indent_textarea);
    }
}
