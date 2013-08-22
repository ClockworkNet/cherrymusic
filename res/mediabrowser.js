//
// CherryMusic - a standalone music server
// Copyright (c) 2012 Tom Wallroth & Tilman Boerner
//
// Project page:
//   http://fomori.org/cherrymusic/
// Sources on github:
//   http://github.com/devsnd/cherrymusic/
//
// licensed under GNU GPL version 3 (or later)
//
// CherryMusic is based on
//   jPlayer (GPL/MIT license) http://www.jplayer.org/
//   CherryPy (BSD license) http://www.cherrypy.org/
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>
//

/********
RENDERING
********/

MediaBrowser = function(cssSelector, json, isplaylist, playlistlabel, parent){
    "use strict";
    this.listing_data_stack = [json];
    this.parent = parent;
    this.cssSelector = cssSelector;

    var self = this;
    
    var listdirclick = function(){
        "use strict";
        $(self.cssSelector + " > .cm-media-list").animate({left: '-100%'}, {duration: 1000, queue: false});
        
        var directory = $(this).attr("dir");
        var compactlisting = $(this).is("[filter]");
        var action = 'listdir';
        var dirdata = {'directory' : directory};
        if(compactlisting){
            action = 'compactlistdir';
            dirdata['filter'] = $(this).attr("filter");
        }
        var currdir = this;
        var success = function(data){
            var json = jQuery.parseJSON(data);
            self.listing_data_stack.push(json)
            self.render();
        };
        busy($(currdir).parent()).hide().fadeIn();
        api({action: action,
             value: JSON.stringify(dirdata)},
            success,
            errorFunc('unable to list compact directory'),
            function(){busy($(currdir).parent()).fadeOut('fast')});
        $(this).blur();
        return false;
    }
    
    this.render = function(){
        var stack_top = self.listing_data_stack[self.listing_data_stack.length-1];
        //split into categories:
        var folders = [];
        var files = [];
        var compact = [];
        var playlist = []
        for(var i=0; i < stack_top.length; i++){
            var e = stack_top[i];
            if("file" == e.type){
                files.push(e);
            } else if("dir" == e.type){
                folders.push(e);
            } else if("compact" == e.type){
                compact.push(e);
            } else if("playlist" == e.type){
                playlist.push(e);
            } else {
                window.console.error('unknown media browser item '+e.type);
            }
        }
        var filehtml = MediaBrowser.static._renderList(files);
        var folderhtml = MediaBrowser.static._renderList(folders);
        var compacthtml = MediaBrowser.static._renderList(compact);
        var playlisthtml = MediaBrowser.static._renderList(playlist);
        
        var html = '';
        if('' != filehtml){
            html += '<h3>Tracks</h3><ul class="cm-media-list">'+filehtml+'</ul>';
        }
        if('' != folderhtml){
            html += '<h3>Collections</h3><ul class="cm-media-list">'+folderhtml+'</ul>';
        }
        if('' != compacthtml){
            html += '<h3>Compact</h3><ul class="cm-media-list">'+compacthtml+'</ul>';
        }
        if('' != playlisthtml){
            html += '<h3>Playlists</h3><ul class="cm-media-list">'+playlisthtml+'</ul>';
        }
        if('' == html){
            html = '<ul class="cm-media-list">'+MediaBrowser.static._renderMessage('No playable media files here.')+'</ul>';
        }
        
        $(self.cssSelector).html(html);
        if(self.listing_data_stack.length > 1){
            var node = $('<div class="cm-media-list-item cm-media-list-parent-item">'+
            '   <a class="cm-media-list-parent" href="javascript:;">'+
            '   <span class="glyphicon glyphicon-arrow-left"></span>'+
            '</a></div>');
            node.on('click',function(){
                self.listing_data_stack.pop();
                self.render();
            });
            $(this.cssSelector).prepend(node);
        }
        playlistManager.setTrackDestinationLabel();
        MediaBrowser.static.albumArtLoader(cssSelector);
    }
    
    this.render();
    $(cssSelector).off('click');
    $(cssSelector).on('click', '.list-dir', listdirclick);
    $(cssSelector).on('click', '.compact-list-dir', listdirclick);
    $(cssSelector).on('click', '.musicfile', MediaBrowser.static.addThisTrackToPlaylist);
    $(cssSelector).on('click', '.addAllToPlaylist', function() {
        if(isplaylist){
            var pl = playlistManager.newPlaylist([], playlistlabel);
        } else {
            var pl = playlistManager.getEditingPlaylist();
        }
        MediaBrowser.static._addAllToPlaylist($(this), pl.id);
        if(isplaylist){
            pl.setSaved(true);
        }
        $(this).blur();
        return false;
    });
    
   
}
MediaBrowser.static = {
    _renderList: function (l){
        "use strict";
        var self = this;
        var html = "";
        var foundMp3 = false;
        $.each(l, function(i, e) {
            if("file" == e.type){
                foundMp3 = true;
                return false;
            }
        });
        var addAll = '';
        if(foundMp3){
            addAll =    '<li><a class="cm-media-list-item addAllToPlaylist" href="javascript:;">'+
                            '<span class="add-track-destination">load playlist</span>'+
                        '</a></li>';
        }
        $.each(l, function(i, e) {
            switch(e.type){
                case 'dir': 
                    html += MediaBrowser.static._renderDirectory(e);
                    break;
                case 'file':
                    html += MediaBrowser.static._renderFile(e);
                    break;
                case 'compact':
                    html += MediaBrowser.static._renderCompactDirectory(e);
                    break;
                case 'playlist':
                    html += MediaBrowser.static._renderPlaylist(e);
                    break;
                default:
                    window.console.log('cannot render unknown type '+e.type);
            }
        });
        return html;
    },
    
    _renderMessage : function(msg){
        return [
            '<li class="fileinlist cm-media-list-item">',
                '<div style="text-align: center">'+msg+'</div>',
            '</li>'
        ].join('');
    },
    _renderFile : function(json){
        return Mustache.render([
            '<li class="fileinlist cm-media-list-item">',
                '<a title="{{label}}" href="javascript:;" class="musicfile" path="{{fileurl}}">',
                    '<span class="glyphicon glyphicon-music"></span>',
                    '<span class="simplelabel">',
                        '{{label}}',
                    '</span>',
                    '<span class="fullpathlabel">',
                        '{{fullpath}}',
                    '</span>',
                    
                '</a>',
            '</li>'
        ].join(''),
        {
            fileurl : json.urlpath,
            fullpath: json.path,
            label: json.label,
        });
    },
    _renderDirectory : function(json){
        return Mustache.render([
            '<li class="list-dir-item cm-media-list-item">',
                '<a dir="{{dirpath}}" href="javascript:;" class="list-dir">',
                    '{{^isrootdir}}',
                            '{{{coverartfetcher}}}',
                    '{{/isrootdir}}',
                    '<div class="list-dir-name-wrap">',
                        '<span class="list-dir-name">{{label}}</span>',
                    '</div>',
                '</a>',
            '</li>',
        ].join(''),
        {
            isrootdir: json.path && !json.path.indexOf('/')>0,
            dirpath: json.path,
            label: json.label,
            coverartfetcher: function(){
                return MediaBrowser.static._renderCoverArtFetcher(json.path)
            },
        });
    },
    _renderPlaylist : function(e){
        return Mustache.render([
           '<li class="playlist-browser-list-item" id="playlist{{playlistid}}">',
                '<div class="playlist-browser-list-item-container">',
                    '<div>',
                        '<div class="playlisttitle">',
                            '<a href="javascript:;" onclick="loadPlaylist({{playlistid}}, \'{{playlistlabel}}\')">',
                            '{{playlistlabel}}',
                            '</a>',
                        '</div>',
                        '<div class="ispublic">',
                            '{{#isowner}}',
                            '<span class="label {{publiclabelclass}}">',
                                'public',
                                '<input onchange="changePlaylist({{playlistid}},\'public\',$(this).is(\':checked\'))" type="checkbox" {{publicchecked}}>',
                            '</span>',
                            '{{/isowner}}',                   
                        '</div>',
                        '{{{usernamelabel}}}',
                        
                        '{{#candelete}}',
                        '<div class="deletebutton">',
                            '<a href="javascript:;" class="btn btn-xs btn-danger" onclick="confirmDeletePlaylist({{playlistid}}, \'{{playlistlabel}}\')">x</a>',
                        '</div>',
                        '{{/candelete}}',
                    '</div>',
                '</div>',
                '<div class="playlistcontent">',
                '</div>',
            '</li>'
        ].join(''),
        {
            playlistid: e['plid'],
            isowner: e.owner,
            candelete: e.owner || isAdmin, 
            playlistlabel:e['title'],
            username: e['username'],
            usernamelabel: renderUserNameLabel(e['username']),
            publicchecked: e['public'] ? 'checked="checked"' : '',
            publiclabelclass : e['public'] ? 'label-success' : 'label-default',
        });
    },
    _renderCompactDirectory : function(json){
        return Mustache.render([
        '<li class="compact-list-item cm-media-list-item">',
           '<a dir="{{filepath}}" filter="{{filter}}" href="javascript:;" class="compact-list-dir">',
                '{{filterUPPER}}',
            '</a>',
        '</li>',
        ].join(''),
        {
            filepath: json.urlpath,
            filter: json.label,
            filterUPPER: json.label.toUpperCase(),
        });
    },
    
    _renderCoverArtFetcher : function(path){
        "use strict";
        var searchterms = encodeURIComponent(JSON.stringify({'directory' : path}))
        return ['<div class="list-dir-albumart unloaded" search-data="'+searchterms+'">',
        '<img src="/res/img/folder.png" width="80" height="80" />',
        '</div>'].join('');
    },
        
    addThisTrackToPlaylist : function(){
        "use strict"
        playlistManager.addSong( $(this).attr("path"), $(this).attr("title") );
        $(this).blur();
        return false;
    },
    
    _addAllToPlaylist : function($source, plid){
        "use strict";
        $source.parent().siblings('li').children('.mp3file').each(function(){
            playlistManager.addSong( $(this).attr("path"), $(this).attr("title"), plid );
        });
    },
    
    albumArtLoader: function(cssSelector){
        "use strict";
        var winpos = $(window).height()+$(window).scrollTop();
        $('.list-dir-albumart.unloaded').each(
            function(idx){
                if($(this).position().top < winpos){
                   $(this).find('img').attr('src', 'api/fetchalbumart/'+$(this).attr('search-data'));
                   $(this).removeClass('unloaded');
                }
            }
        );
    }
}