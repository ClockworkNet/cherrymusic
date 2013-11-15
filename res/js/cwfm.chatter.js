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
            $scope.messages   =  rsp;
            $scope.last_time  =  +new Date;
            setTimeout( refresh, $scope.polling );
        });
        request.error( function( rsp ) {
        });
    };

    $scope.send  =  function( ) {
        var apiurl  = '/api/say/' + $roomservice.get_name( );
        var data    = { 'msg': $scope.message };
        $http({
            method : 'POST'
            , url  : apiurl
            , data : $.param( { value : data } )
            , headers : {'Content-Type': 'application/x-www-form-urlencoded'}
        }).success( function( ) {
            $scope.message  =  '';
        });
    };

    refresh( );
};
