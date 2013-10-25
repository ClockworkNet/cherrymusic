if ( typeof cwfm == 'undefined' ) var cwfm  =  {};

cwfm.playlist       =  {};
cwfm.playlist.ctrl  =  function( $scope, $http, $roomservice ) {

    var nothing  =  function( rsp ) { };

    // @todo
    var on_saveplaylist  =  nothing;
    var on_generaterandomplaylist  =  nothing;
    var on_deleteplaylist  =  nothing;
    var on_changeplaylist  =  nothing;

    var on_search  =  function( rsp ) {
        console.info('search results', rsp);
        $scope.results  =  rsp;
    };

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

    var on_addplaylistsong  =  function( rsp ) {
        console.info('addplaylistsong returned', rsp);
        $scope.songs  =  rsp;
    };

    var on_songchange  =  function( old_song, new_song ) {
        if ( ! $scope.selected ) return;
        api( 'loadplaylist', $scope.selected, on_loadplaylist )
    };

    var init  =  function( ) {
        $scope.roomname  =  $roomservice.get_name( );

        $roomservice.on( 'songchange', on_songchange, $scope );
        $scope.$watch( 'query', $scope.search );

        api( 'showplaylists', on_showplaylists );
    };

    var api  =  function( ) {
        var args    =  Array.prototype.slice.call( arguments, 0 );
        var action  =  args.shift( );
        var apiurl  =  '/api/' + action + '/';
        var data    =  null;
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
                    if ( arg instanceof Array ) {
                        apiurl += arg.join( '/' ) + '/';
                    }
                    else {
                        data = JSON.stringify( arg );
                    }
                    break;
            }
        }
        if ( data ) {
            console.info('POST', apiurl, data);
            $http({
                method : 'POST'
                , url  : apiurl
                , data : $.param( { value : data } )
                , headers : {'Content-Type': 'application/x-www-form-urlencoded'}
            }).success( done );
        }
        else {
            console.info('GET', apiurl);
            $http.get( apiurl ).success( done );
        }
    };

    $scope.select  =  function( pl ) {
        $scope.selected = pl.plid;
        api( 'selectplaylist', [ $scope.roomname, pl.plid ], on_selectplaylist );
    };

    $scope.search  =  function( ) {
        var terms  =  $scope.query;
        if ( ! terms || terms.length < 2 ) {
            $scope.results  =  [];
            return;
        }
        api( 'search', [ terms ], on_search );
    };

    $scope.addsong  =  function( song ) {
        if ( ! $scope.selected ) {
            console.warn( 'No playlist selected' );
            return;
        }
        var data  =  { 
            plid   : $scope.selected
            , song : song
        };
        api( 'addplaylistsong', data, on_addplaylistsong );
    };

    init( );
}
