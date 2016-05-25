/*Pusher.log = function(message) {
  if (window.console && window.console.log) {
    console.log(message);
  }
};*/

// initialize Pusher listener
/*var pusher = new Pusher(window.pusher_key);
var channel = pusher.subscribe(window.channel);
channel.bind('console_msg', function(data) {
    data.source = "Server";
    add_message(data);
});
channel.bind('pusher:subscription_succeeded', function() {
    add_client_message("Subscription succeeded.");
});
*/

/*function add_client_message(message) {
    data = {};
    data.message = message;
    var now = NDateTime.Now();
    data.datetime = now.ToString("yyyy-MM-dd HH:mm:ss.ffffff");
    data.class = "info";
    data.source = "Client";
    add_message(data);
}

function add_message(data) {
    $("div#messages").prepend("<p class='"+data.class+"'>"+data.datetime+" : "+data.source+" : "+data.message+"</p>");
    $("div#messages p").slice(7).remove();
}*/

function redirect(location) {
    window.location = location;
}

$(function() {
    // edit
    /*$("button#edit_html").click(function(event) {
       event.preventDefault();
       $("form#edit_html").find("div.CodeMirror").toggle();
    });*/

    /*$("form").find("div.CodeMirror").toggle();
    $("button[id^=edit_exec").click(function(event) {
       id = event.currentTarget.id;
       $("form#"+id).find("div.CodeMirror").toggle();
       event.preventDefault();
    });*/

    /*$("button[id^=delete_exec").click(function(event) {
      exec_name = $(event.currentTarget).attr('exec');
       event.preventDefault();
          $.post("/fastapp/"+window.active_base+"/delete/"+exec_name+"/", function(xhr, textStatus){
            location.reload();
          });

    });*/

    /*$("button[id^=clone_exec").click(function(event) {
      exec_name = $(event.currentTarget).attr('exec');
       event.preventDefault();
       console.log(event.currentTarget);
       $.post("/fastapp/"+window.active_base+"/clone/"+exec_name+"/", function(data) {
          if (data.redirect) {redirect(data.redirect); }
       });
    });*/

    /*$("button[id^=exec").click(function(event) {
      exec_name = $(event.currentTarget).attr('exec');
       event.preventDefault();
       $.get("/fastapp/"+window.active_base+"/exec/"+exec_name+"/?json", function(data) {
       });
    });*/

    /*$("button[id=create_exec").click(function(event) {
      parent = $(event.currentTarget).parent();
      input = $('<div class="row"> <div class="col-lg-6"> <div class="input-group"> <input type="text" class="form-control"> <span class="input-group-btn"> <button class="btn btn-default" type="button"><span class="glyphicon glyphicon-save"></span> Save</button> </span> </div>');
      parent.after(input);
      event.preventDefault();
      input.find("button").click(function(event) {
          input_value = input.find("input").val();
          $.post("/fastapp/"+window.active_base+"/create_exec/", {'exec_name': input_value}, function(xhr, textStatus){
            location.reload();
          });
      });
    });
    */
    
    /*$("button[id^=rename_exec").click(function(event) {
      parent = $(event.currentTarget).parent();
      exec_name = $(event.currentTarget).attr('exec');
      input = $('<div class="row"> <div class="col-lg-6"> <div class="input-group"> <input type="text" value="'+exec_name+'" class="form-control"> <span class="input-group-btn"> <button class="btn btn-default" type="button"><span class="glyphicon glyphicon-save"></span> Save</button> </span> </div>');
      parent.after(input);
      input.find("button").click(function(event) {
          input_value = input.find("input").val();
          $.post("/fastapp/"+window.active_base+"/rename/"+exec_name+"/", {'new_name': input_value}, function(xhr, textStatus){
            location.reload();
          });
      });
      event.preventDefault();
    });
    */

    /*$("button[id^=rename_base").click(function(event) {
      parent = $(event.currentTarget).parent();
      base_name = window.active_base;
      input = $('<div class="row"> <div class="col-lg-6"> <div class="input-group"> <input type="text" value="'+base_name+'" class="form-control"> <span class="input-group-btn"> <button class="btn btn-default" type="button"><span class="glyphicon glyphicon-save"></span> Save</button> </span> </div>');
      parent.after(input);
      input.find("button").click(function(event) {
          input_value = input.find("input").val();
          $.post("/fastapp/"+window.active_base+"/rename/", {'new_name': input_value}, function(data){
          if (data.redirect) {redirect(data.redirect); }
          });
      });
      event.preventDefault();
    });*/

    //function redirect(xhr,textStatus) {
    // if (xhr.status == 302) {
    //  //location.href = xhr.getResponseHeader("Location");
    //}
  //}

    // shared
    $("button#share").click(function(event) {
      event.preventDefault();
      add_client_message('Access the shared base: <a href="'+window.shared_key_link+'">'+ window.shared_key_link+'</a>');
    });
    // delete base
    $("button#delete").click(function(event) {
      event.preventDefault();
      $.post("/fastapp/"+window.active_base+"/delete/", function(data) {
        if (data.redirect) {redirect(data.redirect); }
        });
    });

    /*// call exec simple
    $("a.exec").click(function(event) {
       event.preventDefault();
       var url = $(this).attr('href');
       $.get(url, function(data) {
       });
    });*/

    // new base
    /*$("button#new_base").click(function(event) {
      new_base = $(event.currentTarget).parent().siblings("input").val();
      $.post("/fastapp/base/new/", {'new_base_name': new_base}, function(data){
        if (data.redirect) {
          redirect(data.redirect);
        }
      });
    });
    */

    // forms
    $("form").submit(function(event) {
        console.warn(event.currentTarget.method);
        if (event.currentTarget.method == "post") {
            $.post(event.currentTarget.action, $(this).serialize(), function(data){
              console.log("send form with POST");
              console.log(data);
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