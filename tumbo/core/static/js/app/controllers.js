  function add_message(data) {
      $("div#messages").prepend("<p class='" + data.class + "'>" + data.datetime +
          " : " + data.source + " : " + data.message + "</p>");
      $("div#messages p").slice(7).remove();
  }

  function add_client_message(message) {
      data = {};
      data.message = message;

      var now = NDateTime.Now();
      data.datetime = now.ToString("yyyy-MM-dd HH:mm:ss.ffffff");
      data.class = "info";
      data.source = "Client";
      add_message(data);
  }



  window.app = angular.module('execApp', ['ngGrid', 'base64', 'ngResource',
      'baseServices', 'angularFileUpload', 'ngCookies',
      'ui.bootstrap', 'xeditable'
  ]);


  window.app.run(function(editableOptions) {
      editableOptions.theme = 'bs3';
  });


  window.app.directive('focusMe', function($timeout, $parse) {
      return {
          //scope: true,   // optionally create a child scope
          link: function(scope, element, attrs) {
              var model = $parse(attrs.focusMe);
              scope.$watch(model, function(value) {
                  if (value === true) {
                      $timeout(function() {
                          element[0].focus();
                      });
                  }
              });
              // to address @blesh's comment, set attribute value to 'false'
              // on blur event:
              element.bind('blur', function() {
                  scope.$apply(model.assign(scope, false));
              });
          }
      };
  });

  window.app.controller('BasesCtrl', ['$scope', 'Bases', 'Base', 'Apy',
      'PublicApy',
      '$upload', '$cookies', '$window', '$http', '$document',
      function($scope, Bases, Base, Apy, PublicApy, $upload, $cookies,
          $window,
          $http,
          $document) {
          $scope.init = function() {
              var bases = Bases.all(function() {
                  angular.forEach(bases, function(base) {
                      base.apy_models = Apy.all({
                          'name': base.name
                      });
                  });
                  $scope.bases = bases;
              });
          };

          $scope.public_apys = PublicApy.all();


          /*$scope.$watch("bases", function(newvalue) {
              console.log("Changed to " + newvalue);
          });
            */


          $scope.relate = function(apy) {
              console.info(apy);
              console.info($scope.base);
              if ($scope.base.foreign_apys.indexOf(apy.url) == -1) {
                  $scope.base.foreign_apys.push(apy.url);
              } else {
                  var index = $scope.base.foreign_apys.indexOf(apy.url);
                  $scope.base.foreign_apys.splice(index, 1);
              }

              $scope.base.$update({
                  'name': $scope.base.name
              });

          }

          $scope.is_related = function(apy) {
                if ($scope.base.foreign_ays != undefined) {
                    return !($scope.base.foreign_apys.indexOf(apy.url) == -1);
                };
          }

          //if (!angular.isUndefined(window.active_base_id)) {
          if (window.active_base_id.length !== 0) {
              $scope.base = Base.get({
                  'name': window.active_base
              });
          }

          $scope.creation_running = function() {
              return ($scope.creation_is_running);
          };

          $scope.submit_new_base = function(e) {
              e.preventDefault();
              $scope.creation_is_running = true;
              $http({
                  method: 'POST',
                  url: 'base/new',
                  data: $.param({
                      'new_base_name': this.new_base_name
                  }), // pass in data as strings
                  headers: {
                      'Content-Type': 'application/x-www-form-urlencoded'
                  } // set the headers so angular passing info as form data (not request payload)
              }).success(function(data, status, headers, config) {
                  $document.find('form#new_base div').append(
                      angular.element(
                          '<span class="help-block">Base created</span>'
                      ));
                  $document.find('form#new_base').addClass(
                      'has-success');
                  $scope.new_base_name = "";
                  $scope.bases.push(data);
              }).error(function(data, status, headers, config) {
                  // quota exceeded or already existant
                  $document.find('form#new_base div').append(
                      angular.element(
                          '<span class="help-block">' +
                          data + '</span>'));
                  $document.find('form#new_base').addClass(
                      'has-warning');
              });
              $scope.creation_is_running = false;
          };

          $scope.updatePublicity = function(base) {
              $.post("/core/dashboard/" + base.name + "/sync/", {
                  public: base.public,
                  static_public: base.static_public
              });
          };

          $scope.cycle_state = function(base) {
              if (base.state) {
                  Base.stop({
                      name: base.name
                  }, base, function(data) {
                      base.state = false;
                  });
              }
              if (!base.state) {
                  Base.start({
                      name: base.name
                  }, base, function(data) {
                      base.state = true;
                      base.executors = data['executors'];
                  });
              }
          };

          $scope.restart = function(base) {
              if (base.state === true) {
                  Base.restart({
                      name: base.name
                  }, base);
              }
          };

          $scope.destroy = function(base) {
              if (base.executors.length > 0 ) {
                  Base.destroy({
                      name: base.name
                  }, base, function(data) {
                      base.state = false;
                      base.executors = [];
                  });
              }
          };


          $scope.onFileSelect = function($files) {
              //$files: an array of files selected, each file has name, size, and type.
              for (var i = 0; i < $files.length; i++) {
                  var file = $files[i];
                  $scope.upload = $upload.upload({
                      url: '/core/api/base/import', //upload.php script, node.js route, or servlet url
                      //method: 'POST' or 'PUT',
                      //headers: {'header-key': 'header-value'},
                      //withCredentials: true,
                      headers: {
                          'X-CSRFToken': $cookies.csrftoken
                      },
                      data: {
                          attachment: $scope.myModelObj,
                          name: $scope.name
                      },
                      file: file, // or list of files ($files) for html5 only
                      //fileName: 'doc.jpg' or ['1.jpg', '2.jpg', ...] // to modify the name of the file(s)
                      // customize file formData name ('Content-Disposition'), server side file variable name.
                      //fileFormDataName: myFile, //or a list of names for multiple files (html5). Default is 'file'
                      // customize how data is added to formData. See #40#issuecomment-28612000 for sample code
                      //formDataAppender: function(formData, key, val){}
                  }).progress(function(evt) {
                      console.log('percent: ' + parseInt(
                          100.0 * evt.loaded / evt.total
                      ));
                  }).success(function(data, status, headers,
                      config) {
                      // file is uploaded successfully
                      $window.location = "/core/" + data
                          .name + "/index/";

                  });
                  //.error(...)
                  //.then(success, error, progress);
                  // access or attach event listeners to the underlying XMLHttpRequest.
                  //.xhr(function(xhr){xhr.upload.addEventListener(...)})
              }
              /* alternative way of uploading, send the file binary with the file's content-type.
  			   Could be used to upload files to CouchDB, imgur, etc... html5 FileReader is needed.
  			   It could also be used to monitor the progress of a normal http post/put request with large data*/
              // $scope.upload = $upload.http({...})  see 88#issuecomment-31366487 for sample code.
          };

      }
  ]);


  window.app.controller('ExecCtrl', ['$rootScope', '$scope', '$http',
      '$base64',
      'Apy', 'PublicApy', 'Apy1',
      function($rootScope, $scope, $http, $base64, Apy, PublicApy, Apy1) {
          $scope.new_exec_name = "";
          $scope.apys = [];


          $scope.alerts = [];

          $scope.closeAlert = function(index) {
              $scope.alerts.splice(index, 1);
          };

          $scope.init = function() {
              var apys = Apy.all({
                  'name': window.active_base
              }, function() {
                  $scope.apys = apys;
                  counter = 0;

                  $scope.apys.map(function(apy) {
                      $scope.$watch(apy, function(
                          changed) {
                      }, true);
                      counter++;
                  });
              });


              // setup pusher for listening to counter events
              /*
  			Pusher.subscribe(window.channel, "counter", function(item) {
  				console.log(item);
  				$scope.apys.map(function(apy) {
  					if (apy.id == item['apy_id']) {
  						apy.counter = item['counter'];
  					}
  				});
  			});

  			Pusher.subscribe(window.channel, 'pusher:subscription_succeeded',
  				function(members) {
  					console.log("subscription_succeeded");
  					console.log(members);
  					add_client_message("Subscription succeeded.");
  				});
                  */
          };

          /*
  		Pusher.subscribe(window.channel, 'console_msg', function(data) {
  			data.source = "Server";
  			add_message(data);
  		});
          */

          $scope.blur = function(apy, $event) {
              $scope.save(apy);
          };

          $scope.create = function() {
              Apy.create({
                  'name': window.active_base
              }, {
                  'name': $scope.new_exec_name
              }, function(apy) {
                  $scope.apys.push(apy);
                  $scope.showNewExec = false;
              });
          };

          $scope.save = function(apy) {
              Apy1.update({
                  'base_name': window.active_base,
                  'name': apy.name
              }, apy).$promise.then(function(data) {
                  $scope.alerts.push({
                      type: 'success',
                      msg: "Exec '" + apy.name +
                          "' saved"
                  });
              }, function(data) {
                  $scope.alerts.push({
                      type: 'danger',
                      msg: "Exec '" + apy.name +
                          "' not saved"
                  });
                  console.error("error");
                  console.error(data);
                  angular.forEach(data.data.detail.errors,
                      function(value, key) {
                          $scope.alerts.push({
                              type: 'danger',
                              msg: value.filename +
                                  ":" + value.lineno +
                                  ":" + value.col +
                                  ": " + value.msg
                          });
                      });
                  angular.forEach(data.data.detail.warnings,
                      function(value, key) {
                          $scope.alerts.push({
                              type: 'warning',
                              msg: value.filename +
                                  ":" + value.lineno +
                                  ":" + value.col +
                                  ": " + value.msg
                          });
                      });
              });
          };

          $scope.delete = function(apy) {
              //Apy1.update({'baseId': window.active_base_id, 'id': apy.id}, apy);
              console.info(apy);
              Apy1.delete({
                  'base_name': window.active_base,
                  'name': apy.name
              }, function(data) {
                  var indx = $scope.apys.indexOf(apy);
                  $scope.apys.splice(indx, 1);
              });

          };

          $scope.clone = function(apy) {
              Apy1.clone({
                  'base_name': window.active_base,
                  'name': apy.name
              }, apy, function(data) {
                  $scope.apys.push(data);
              });
          };

          $scope.executeNewWindow = function(apy) {
              window.open("/core/api/base/" + window.active_base +
                  "/apy/" + apy.name + "/execute/?json=",
                  "_blank");
          };

          $scope.printcurl = function(apy) {
              var parser = document.createElement('a');
              parser.href = document.URL;
              add_client_message("user:   curl -u " + window.username +
                  " -H'Cookie: " + document.cookie + "' \"" +
                  parser.protocol + "//" +
                  parser.host + "/core/" + window.active_base +
                  "/exec/" + apy.name +
                  "/?json=\"");
              shared_key = window.shared_key_link.split("?")[1];
              add_client_message("anonym: curl \"" + parser.protocol +
                  "//" + parser
                  .host +
                  "/core/base/" + window.active_base +
                  "/exec/" + apy.name +
                  "/?json=&" + shared_key + "\"");
          };

          $scope.rename = function($event) {
              new_exec_name = $($event.currentTarget.parentNode.parentNode)
                  .find(
                      'input').first().val();
              this.apy.name = new_exec_name;
              this.apy.$save();
          };
      }
  ]);

  var removeTemplate =
      '<button type="button" class="btn btn-default btn-xs" ng-click="delete()"><span class="glyphicon glyphicon-remove"></span> Delete</button>';
  window
      .app.controller('SettingsCtrl', ['$scope', '$http', '$base64',
          'Settings', 'Setting',
          function($scope, $http, $base64, Settings, Setting) {
              $scope.myData = [];
              //$scope.publicSelectEditableTemplate = '<select ng-class="\'colt\' + col.index" ng-input="COL_FIELD" ng-model="COL_FIELD" ng-options="id as name for (id, name) in statuses" ng-blur="updateEntity(row)" />';
              //$scope.publicSelectEditableTemplate = '<input type="checkbox" ng-model="row.entity.public" ng-true-value="\'true\'" ng-false-value="\'false\'">';
              $scope.publicSelectEditableTemplate =
                  '<input type="checkbox" ng-model="row.entity.public">';
              $scope.gridOptions = {
                  data: 'myData',
                  selectedItems: [],
                  enableSorting: true,
                  //sortInfo: {fields: ['key', 'value'], directions: ['asc']},
                  //enableCellSelection: true,
                  enableRowSelection: false,
                  //enableCellEditOnFocus: false,
                  columnDefs: [{
                      field: 'key',
                      displayName: 'Key',
                      enableCellEdit: true,
                      width: 120
                  }, {
                      field: 'value',
                      displayName: 'Value',
                      enableCellEdit: true,
                      editableCellTemplate: '<textarea row="1"  ng-class="\'colt\' + col.index" ng-input="COL_FIELD" ng-model="COL_FIELD" />'
                  }, {
                      field: 'public',
                      displayName: 'Public',
                      cellTemplate: $scope.publicSelectEditableTemplate
                  }, {
                      field: 'actions',
                      displayName: '',
                      enableCellEdit: false,
                      cellTemplate: removeTemplate
                  }]
              };

              $scope.init = function() {
                  $scope.myData = Settings.all({
                      'name': window.active_base
                  });
              };

              $scope.addRow = function() {
                  $scope.myData.push({
                      key: "key",
                      value: "value"
                  });
              };

              $scope.save = function() {
                  // base64 output
                  $scope.myData.map(function(item) {
                      if (item.id === undefined) {
                          new_item = Settings.create({
                              'name': window.active_base
                          }, item, function() {
                              if (new_item['id'] !==
                                  undefined) {
                                  item.id = new_item[
                                      'id'];
                              }
                          });

                      } else {
                          Setting.update({
                              'name': window.active_base,
                              'id': item.id
                          }, item);
                      }
                  });
              };

              $scope.delete = function() {
                  var index = this.row.rowIndex;
                  $scope.gridOptions.selectItem(index, false);
                  removed = $scope.myData.splice(index, 1)[0];
                  Setting.delete({
                      'name': window.active_base,
                      'id': removed.id
                  });
              };
          }
      ]);

  window.app.directive('codemirror', function() {
      return {
          restrict: 'A',
          priority: 2,
          scope: {
              'apy': '=codemirror'
          },
          template: '{{apy.module}}',
          link: function(scope, elem, attrs) {
              //console.log(scope);
              //console.log(scope.apy);
              var myCodeMirror = CodeMirror(function(elt) {
                  elem.parent().replaceWith(elt);
              }, {
                  value: scope.apy.module,
                  mode: {
                      name: "text/x-cython",
                      version: 2,
                      singleLineStringErrors: false
                  },
                  //readOnly: "$window.readyOnly",
                  lineNumbers: true,
                  indentUnit: 4,
                  tabMode: "shift",
                  lineWrapping: true,
                  indentWithTabs: true,
                  matchBrackets: true,
                  vimMode: true,
                  showCursorWhenSelecting: true
              });
              myCodeMirror.on("blur", function(cm, cmChangeObject) {
                  console.log("scope.$apply");
                  scope.$apply(function() {
                      scope.apy.module =
                          myCodeMirror.getValue();
                  });
              });
          }
      };
  });

  //  var FooControllers = angular.module('FooControllers', []);

 

  window.app.controller('TransportEndpointCtrl', ['$scope', '$filter', '$q',
      '$http', '$timeout', 'TransportEndpoints', 'Base',
      function($scope, $filter, $q, $http, $timeout, TransportEndpoints,
          Base) {

          var itemsPendingSave = [];

          $scope.transport = function(transport, base) {
              Base.transport({
                  name: window.active_base
              }, transport);

          };

          $scope.statuses = [{
              value: 1,
              text: 'status1'
          }, {
              value: 2,
              text: 'status2'
          }, {
              value: 3,
              text: 'status3'
          }, {
              value: 4,
              text: 'status4'
          }];

          /*$scope.groups = [];
  		$scope.loadGroups = function() {
  		  return $scope.groups.length ? null : $http.get('/groups').success(function(data) {
  		    $scope.groups = data;
  		  });
  		};*/

          $scope.endpoints = TransportEndpoints.query();

          $scope.showGroup = function(user) {
              if (user.group && $scope.groups.length) {
                  var selected = $filter('filter')($scope.groups, {
                      id: user.group
                  });
                  return selected.length ? selected[0].text :
                      'Not set';
              } else {
                  return user.groupName || 'Not set';
              }
          };

          /*$scope.showStatus = function(user) {
  		  var selected = [];
  		  if(user.status) {
  		    selected = $filter('filter')($scope.statuses, {value: user.status});
  		  }
  		  return selected.length ? selected[0].text : 'Not set';
  		};*/

          /*  $scope.checkName = function(data) {
  		    console.log("user.name.onbeforesave:", data);
  		    if (data !== 'awesome') {
  		      return "Username should be `awesome`";
  		    }
  		  };*/

          $scope.cancelChanges = function() {
              /*angular.forEach(itemsPendingSave, function(user){
  			  var index = $scope.users.indexOf(user);
  			  $scope.removeUser(index);
  			});
  			itemsPendingSave = [];
  			$scope.tableform.$cancel();
  			*/
          };

          /*  $scope.removeUser = function(index) {
  		    $scope.users.splice(index, 1);
  		  };*/

          $scope.saveTable = function() {
              //$scope.users already updated

              console.log("tableform.onaftersave");
              var results = [];
              itemsPendingSave = [];
              angular.forEach($scope.endpoints, function(endpoint) {
                  console.log(endpoint);
                  console.log(endpoint.id);
                  if (angular.isUndefined(endpoint.id)) {
                      console.log("create");
                      te = TransportEndpoints.save(endpoint);
                      console.log(te);
                      endpoint.id = te.id;

                  } else {
                      console.log("update");

                      //Setting.update({'baseId': window.active_base_id, 'id': item.id}, item);
                      TransportEndpoints.update({
                          'id': endpoint.id
                      }, endpoint);
                  }
                  //results.push($http.post('/saveUser', user));
              });
              return $q.all(results);
          };

          // add user
          $scope.addEndpoint = function() {
              var newEndpoint = {
                  //id: $scope.users.length,
                  url: '',
                  override_settings_priv: false,
                  override_settings_pub: true,
              };
              $scope.endpoints.push(newEndpoint);
              itemsPendingSave.push(newEndpoint);

              if (!$scope.tableform.$visible) {
                  $scope.tableform.$show();
              }
              // Hack to be able to add a record and have focus set to the new row
              $timeout(function() {
                  newEndpoint.isFocused = true;
              }, 0);
          };
      }
  ]);

  /*    window.app.config(function($resourceProvider) {
        console.log($resourceProvider);
      $resourceProvider.defaults.stripTrailingSlashes = false;
    });
  */

  window.app.config(['$httpProvider', '$cookiesProvider', function(
      $httpProvider, $cookiesProvider) {
      $httpProvider.interceptors.push(function($q, $cookies) {
          return {
              'request': function(config) {
                  //config.url = config.url + '?id=123';
                  if (config.method == "POST" || config
                      .method == "PUT") {
                      config.url = config.url + "/";
                      config.headers['X-CSRFToken'] =
                          $cookies.csrftoken;
                  }
                  return config || $q.when(config);

              }

          }
      });
  }]);


  window.app.filter('reverse', function() {
      return function(items) {
          return items.slice().reverse();
      };
  });

$().ready(function() {

    $( "input#change_password" ).click(function(e) {
          $form = $("form#change_password");
          var post_url = $form.attr("action");
          $.ajax({
            type: "POST",
            url: post_url,
            data: $form.serialize()
          }).done(function(html) {
            // check the html and use that to determine what message to prompt back to your user
            console.info(html);
            if (html == "OK") { 
                $form.html('<div class="alert alert-success"> <a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a> <strong>Password changed!</strong> You need to relogin, thus you will be redirected in 3 seconds!</div>');
                setTimeout(function(){ window.location.href = "/" }, 3000);
            };
          });
        e.preventDefault();
    });

});
