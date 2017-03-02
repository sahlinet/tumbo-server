function add_client_message(message) {
    data = {};
    data.message = message;

    var now = NDateTime.Now();
    data.datetime = now.ToString("yyyy-MM-dd HH:mm:ss.ffffff");
    data.class = "info";
    data.source = "Client";
    add_message(data);
}

function add_message(data) {
    $("div#messages").prepend("<p class='" + data.class + "'>" + data.datetime +
        " : " + data.source + " : " + data.message + "</p>");
    $("div#messages p").slice(7).remove();
}

function output(inp) {
    document.body.appendChild(document.createElement('pre')).innerHTML = inp;
}

function syntaxHighlight(json) {
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return json.replace(
        /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
        function(match) {
            var cls = 'number';
            if (/^"/.test(match)) {
                if (/:$/.test(match)) {
                    cls = 'key';
                } else {
                    cls = 'string';
                }
            } else if (/true|false/.test(match)) {
                cls = 'boolean';
            } else if (/null/.test(match)) {
                cls = 'null';
            }
            return '<span class="' + cls + '">' + match + '</span>';
        });
}

var obj = {
    a: 1,
    'b': 'foo',
    c: [false, 'false', null, 'null', {
        d: {
            e: 1.3e5,
            f: "1.3e5"
        }
    }]
};
/*var str = JSON.stringify(obj, undefined, 4);

output(str);
output(syntaxHighlight(str));*/
