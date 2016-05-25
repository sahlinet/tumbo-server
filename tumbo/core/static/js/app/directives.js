window.app.directive('codemirror', function() {
  return {
    restrict: 'A',
    priority: 2,
    scope: {
        'module': '=codemirror'
    },
    template: '{{module}}',
    link: function(scope, elem, attrs) {
      var myCodeMirror = CodeMirror(function(elt) {
          elem.parent().replaceWith(elt);
        }, {
          value: scope.module,
          mode: {name: "text/x-cython",
          version: 2,
          singleLineStringErrors: false},
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
      myCodeMirror.on("blur", function(cm, cmChangeObject){
          scope.$apply(function() {
            scope.apy.module = myCodeMirror.getValue();
          });
        //scope.apy.$save({'baseId': window.active_base_id, 'id': scope.apy.id});
      });
    }
  };
});
