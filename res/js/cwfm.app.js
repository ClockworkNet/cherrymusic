angular.module( 'cwfmRoomApp', [ 'cwfmFilters' ] )
    .service( '$roomservice', cwfm.room.service )
    .controller( 'cwfmRoomCtrl', [ '$scope', '$http', '$roomservice', cwfm.room.ctrl ] )
    .controller( 'cwfmPlaylistCtrl', [ '$scope', '$http', '$roomservice', cwfm.playlist.ctrl ] );
