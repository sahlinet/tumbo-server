function redirect(location) {
    window.location = location;
}

$(function() {
    // shared
    $("button#share").click(function(event) {
      event.preventDefault();
      add_client_message('Access the shared base: <a href="'+window.shared_key_link+'">'+ window.shared_key_link+'</a>');
    });
    // delete base
    $("button#delete").click(function(event) {
      event.preventDefault();
      $.post("/core/base/"+window.active_base+"/delete/", function(data) {
        if (data.redirect) {redirect(data.redirect); }
        });
    });

    // forms
    $("form").submit(function(event) {
        console.warn(event.currentTarget.method);
        if (event.currentTarget.method == "post") {
            $.post(event.currentTarget.action, $(this).serialize(), function(data){
            });
        } else if (event.currentTarget.method == "get") {
            $.get(event.currentTarget.action, $(this).serialize(), function(data){
                if (data.redirect) {
                  redirect(data.redirect);
                }

            });

                     } else {
            console.error("no method defined on form");
        }
        event.preventDefault();
        return false;

    });
});
