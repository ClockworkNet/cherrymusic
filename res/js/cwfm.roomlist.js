if ( typeof cwfm == 'undefined' ) var cwfm  =  {};

cwfm.roomlist  =  { poll : 1000 };

cwfm.roomlist.ctrl  =  function( $scope, $http, $roomservice ) {

    var init  =  function( ) {
        setInterval( refresh, cwfm.roomlist.poll );
        $scope.rooms  =  [];
    };

    var refresh  =  function( ) {
        $http.get( '/api/rooms/' ).success( function( rsp ) {
            console.info(rsp);
            $scope.rooms = rsp;
        } );
    };

    $scope.make_room  =  function( ) {
        if ( ! $scope.new_room) {
            return;
        }
        window.location  =  '/room/' + $scope.new_room;
    }

    init( );
};

angular.module( 'cwfmMainApp', [ 'cwfmFilters' ] )
    .controller( 'cwfmRoomlistCtrl', [ '$scope', '$http', cwfm.roomlist.ctrl ] )
;
