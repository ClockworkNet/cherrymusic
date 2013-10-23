if ( typeof cwfm == 'undefined' ) var cwfm  =  {};

cwfm.room  =  { ping: 1000 };

cwfm.room.ctrl  =  function( $scope, $http ) {

    var init  =  function( ) {

        // Wrapper for calling jPlayer functions
        $scope.player  =  function( ) {
            $.fn.jPlayer.apply( $( '#jplayer' ), arguments );
        }

        var on_ready  =  function( ) {
            $scope.heartbeat  =  setInterval( function( ) { api( 'roominfo' ) }, cwfm.room.ping );
            $scope.api( 'roominfo' );
        };

        var on_canplay  =  function( e ) {
            if ( ! this.room || ! this.room.song ) return;
            var song  =  this.room.song;
            var time  =  ( Date.now() / 1000 ) - song.started;
            this.player( 'play', time );
        };

        $scope.player({
            ready: on_ready
            , canplay: $.proxy( on_canplay, $scope )
        });
    };


    var get_filetype  =  function( path ) {
        return path.substr( path.lastIndexOf( '.' ) + 1 );
    };


    var song_changed  =  function( old_song, new_song ) {
        if ( new_song.path ) {
            var type  =  get_filetype( new_song.path );
            var data  =  {};
            data[ type ]  =  new_song.path;
            $scope.player( 'setMedia', data );
        }
        else {
            $scope.player( 'clearMedia' );
        }
    };

    var databind  =  function( rsp ) {
        if ( rsp.members ) {
            rsp.members.sort( function( ma, mb ) {
                if ( ma.dj && mb.dj ) return ma.dj - mb.dj;
                if ( ma.dj ) return -1;
                if ( mb.dj ) return 1;
                return ma.joined - mb.joined;
            } );
        }
        var old_song =  $scope.room && $scope.room.song ? $scope.room.song : { path: null };
        var new_song =  rsp && rsp.song ? rsp.song : { path: null };

        $scope.room  =  rsp;

        if ( old_song.path != new_song.path ) {
            song_changed( old_song, new_song );
        }
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
        var path  =  song.relpath;
        return path;
    };

    $scope.song_played  =  function( ) {
        var song  =  $scope.room.song;
        if ( ! song || ! song.length ) return 0;
        var now  =  Date.now() / 1000.0;
        return now - song.started;
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
