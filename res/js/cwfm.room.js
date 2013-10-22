var PING = 1000;

angular.module( 'cwfmFilters', [] )
.filter( 'time', function( ) {
    return function( input ) {
        var pad      =  function( n ) { return n < 10 ? '0' + n : n; }
        var time     =  parseInt( input );
        var hours    =  Math.floor( time / 3600 );
        var minutes  =  Math.floor( time / 60 ) - ( hours * 3600 );
        var seconds  =  time - ( hours * 3600 ) - ( minutes * 60 );
        var d        =  new Date( 0, 0, 0, hours, minutes, seconds );
        if ( hours ) return pad( hours ) + ':' + pad( minutes ) + ':' + pad( seconds );
        return  pad( minutes ) + ':' + pad( seconds );
    };
}).
filter( 'checkmark', function( ) {
    return function( input ) {
        return input ? '\u2713' : '\u2718';
    };
});


var roomApp  =  angular.module( 'cwfmRoomApp', [ 'cwfmFilters' ] );

roomApp.controller( 'cwfmRoomCtrl', [ '$scope', '$http',
function cwfmRoomCtrl( $scope, $http ) {

    var init  =  function( ) {
        $scope.heartbeat  =  setInterval( function( ) { api( 'roominfo' ) }, PING );
        $scope.api( 'roominfo' );
    };

    var databind  =  function( rsp ) {
        $scope.room  =  rsp;
    };

    var api  =  function( action ) {
        var apiurl  = '/api/' + action + '/' + $scope.room.name;
        $http.get( apiurl ).success( databind );
    };

    $scope.room  =  {};
    $scope.room.name  =  location.pathname.substr( location.pathname.indexOf( '/room/' ) + 6 );

    $scope.song_title  =  function( ) {
        var song  =  $scope.room.song;
        if ( ! song ) return '...';
        if ( song.title != '' ) return song.title;
        var path  =  song.path;
        return path;
    };

    $scope.song_remaining  =  function( ) {
        var song  =  $scope.room.song;
        if ( ! song || ! song.length ) return 0;
        var now  =  Date.now() / 1000.0;
        var end  =  song.started + song.length;
        return end - now;
    };

    $scope.dj  =  function( member ) {
        return member.dj != null;
    };

    $scope.api  =  api;

    init( );
}]);
