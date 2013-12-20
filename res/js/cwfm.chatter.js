if ( typeof cwfm == 'undefined' ) var cwfm  =  {};

cwfm.chatter  =  { };

cwfm.chatter.ctrl  =  function( $scope, $http, $roomservice ) {

    $scope.polling    =  1000;
    $scope.last_time  =  null;

    var refresh  =  function( ) {
        var apiurl  =  '/api/chatter/' + $roomservice.get_name( );
        if ( $scope.last_time ) {
            apiurl  +=  '/' + $scope.last_time;
        }

        var request  =  $http.get( apiurl );

        request.success( function( rsp ) {
            if (rsp.length > 0) console.info(rsp);
            if (!$scope.messages) $scope.messages = [];
            for (var i=0; i<rsp.length; i++) {
                $scope.add_message(rsp[i]);
            }
            $scope.last_time  =  +new Date;
            setTimeout( refresh, $scope.polling );
        });
        request.error( function( rsp ) {
        });
    };

    $scope.add_message  =  function( o ) {
        $scope.messages.unshift( o );
    };

    $scope.send  =  function( ) {
        var apiurl  = '/api/say/';
        var msg     = $scope.message;
        var data    = [ $roomservice.get_name( ), msg ];
        $http({
            method : 'POST'
            , url  : apiurl
            , data : $.param( { value : JSON.stringify( data ) } )
            , headers : {'Content-Type': 'application/x-www-form-urlencoded'}
        }).success( function( rsp ) {
            $scope.add_message(rsp);
            $scope.message  =  '';
        });
    };

    refresh( );
};
