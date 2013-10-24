if ( typeof cwfm == 'undefined' ) var cwfm  =  {};

cwfm.playlist       =  {};
cwfm.playlist.ctrl  =  function( $scope, $http, $roomservice ) {

    var nothing  =  function( rsp ) { };

    var on_search  =  nothing;
    var on_saveplaylist  =  nothing;
    var on_generaterandomplaylist  =  nothing;
    var on_deleteplaylist  =  nothing;
    var on_changeplaylist  =  nothing;

    var on_showplaylists  =  function( rsp ) {
        console.info('showplaylists returned', rsp);
        $scope.playlists  =  rsp;
    };

    var on_selectplaylist  =  function( rsp ) {
        console.info('selectplaylist returned', rsp);
        $scope.songs  =  rsp;
    };

    var on_loadplaylist  =  function( rsp ) {
        console.info('loadplaylist returned', rsp);
        $scope.songs  =  rsp;
    };

    var on_songchange  =  function( old_song, new_song ) {
        if ( ! $scope.selected ) return;
        api( 'loadplaylist', $scope.selected, on_loadplaylist )
    };

    var init  =  function( ) {
        $scope.roomname  =  $roomservice.get_name( );
        $roomservice.on( 'songchange', on_songchange, $scope );
        api( 'showplaylists', on_showplaylists );
    };

    var api  =  function( ) {
        var args    =  Array.prototype.slice.call( arguments, 0 );
        var action  =  args.shift( );
        var apiurl  =  '/api/' + action + '/';
        var data    =  {};
        var done    =  nothing;
        var arg     =  null;
        while ( arg = args.shift( ) ) {
            switch ( typeof arg ) {
                case 'function':
                    done = arg;
                    break;
                case 'string':
                case 'number':
                    apiurl += arg + '/';
                    break;
                case 'object':
                    apiurl += arg.join('/') + '/';
                    break;
            }
        }
        console.info('posting', apiurl, data);
        $http.get( apiurl ).success( done );
    };

    $scope.select  =  function( pl ) {
        $scope.selected = pl.plid;
        api( 'selectplaylist', [ $scope.roomname, pl.plid ], on_selectplaylist );
    };

    init( );
}
