angular.module( 'cwfmRoomApp', [ 'cwfmFilters' ] )
    .controller( 'cwfmRoomCtrl', [ '$scope', '$http', cwfm.room.ctrl ] )
    .controller( 'cwfmPlaylistCtrl', [ '$scope', '$http', cwfm.playlist.ctrl ] );
