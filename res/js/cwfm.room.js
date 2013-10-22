if ( typeof cwfm == 'undefined' ) var cwfm  =  {};
cwfm.room  =  { ping: 1000 };
cwfm.room.ctrl  =  function( $scope, $http ) {

    var init  =  function( ) {
        $scope.heartbeat  =  setInterval( function( ) { api( 'roominfo' ) }, cwfm.room.ping );
        $scope.api( 'roominfo' );
    };

    var databind  =  function( rsp ) {
        $scope.room  =  rsp;
        $scope.room.members.sort( function( ma, mb ) {
            if ( ma.dj && mb.dj ) return ma.dj - mb.dj;
            if ( ma.dj ) return -1;
            if ( mb.dj ) return 1;
            return ma.joined - mb.joined;
        } );
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

    $scope.not  =  function( func ) {
        return function( item ) {
            return ! func( item );
        };
    };

    $scope.is_current_dj  =  function( member ) {
        return member.uid == $scope.room.dj;
    };

    $scope.is_dj  =  function( member ) {
        return member.dj != null;
    };

    $scope.api  =  api;

    init( );
};
