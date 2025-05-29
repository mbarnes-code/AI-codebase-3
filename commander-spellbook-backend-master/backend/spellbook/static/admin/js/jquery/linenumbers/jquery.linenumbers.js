(function ($) {
    /** @type {HTMLTextAreaElement} */
    var _buffer;

    /**
    * Returns the number of lines in a textarea, including wrapped lines.
    *
    * __NOTE__:
    * [textarea] should have an integer line height to avoid rounding errors.
    * 
    * Source: https://stackoverflow.com/a/45252226/8589004
    */
    function countLines(textarea, text=null) {
        if (_buffer == null) {
            _buffer = document.createElement('textarea');
            _buffer.style.border = 'none';
            _buffer.style.height = '0';
            _buffer.style.overflow = 'hidden';
            _buffer.style.padding = '0';
            _buffer.style.position = 'absolute';
            _buffer.style.left = '0';
            _buffer.style.top = '0';
            _buffer.style.zIndex = '-1';
            document.body.appendChild(_buffer);
        }
    
        var cs = window.getComputedStyle(textarea);
        var pl = parseInt(cs.paddingLeft);
        var pr = parseInt(cs.paddingRight);
        var lh = parseInt(cs.lineHeight);
    
        // [cs.lineHeight] may return 'normal', which means line height = font size.
        if (isNaN(lh)) lh = parseInt(cs.fontSize);
    
        // Copy content width.
        _buffer.style.width = (textarea.clientWidth - pl - pr) + 'px';
    
        // Copy text properties.
        _buffer.style.font = cs.font;
        _buffer.style.letterSpacing = cs.letterSpacing;
        _buffer.style.whiteSpace = cs.whiteSpace;
        _buffer.style.wordBreak = cs.wordBreak;
        _buffer.style.wordSpacing = cs.wordSpacing;
    
        // Copy value.
        _buffer.value = text === null ? textarea.value : text;
    
        var result = Math.floor(_buffer.scrollHeight / lh);
        if (result == 0) result = 1;
        return result;
    }

    $.fn.linenumbers = function(options) {
        if (typeof options === "object" || !options) {
            return this.each(function(_, e) {
                options = $.extend({}, $.fn.linenumbers.defaults, options);
                const $this = $(e);
                $this.wrap(`<div class="${options.editorClass}"></div>`);
                const $editor = $this.parent();
                $editor.prepend(`<div class="${options.lineNumbersClass}"></div>`);
                const $lineNumbers = $editor.find(`div.${options.lineNumbersClass}`);
                function updateLineNumbers() {
                    const children = $lineNumbers.children('span');
                    const currentLineCount = children.length;
                    const currentNewLineCount = children.filter(`.${options.numberClass}`).length;
                    const lines = countLines($this[0]);
                    const rows = $this.val().split('\n') || [];
                    if (rows.length == currentNewLineCount && lines == currentLineCount) {
                        return;
                    }
                    $lineNumbers.empty();
                    for (let i = 0; i < rows.length; i++) {
                        $lineNumbers.append(`<span class="${options.numberClass}"></span>`);
                        const lines = countLines($this[0], rows[i]);
                        for (let j = 0; j < lines - 1; j++) {
                            $lineNumbers.append(`<span></span>`);
                        }
                    }
                }
                updateLineNumbers();
                $this.on('input', _ => updateLineNumbers());
                const observer = new ResizeObserver(updateLineNumbers);
                $this.each((_, e) => observer.observe(e));
            });
        }
    };

    $.fn.linenumbers.defaults = {
        editorClass: 'editor',
        lineNumbersClass: 'line-numbers',
        numberClass: 'number',
    };
})(django.jQuery);
