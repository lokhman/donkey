+function() {
    'use strict';

    var $window = $(window),
        $document = $(document),
        $uptime = $('.uptime'),
        $loader = $('.loader'),
        $main = $('#_main'),
        $upload = $('#_upload');

    function ms2time(ms) {
        var x, s, m, h,
            pad = function(n) {
                return n < 10 ? '0' + n : n;
            };

        x = ~~((ms - (ms % 1000)) / 1000);
        s = x % 60;
        x = ~~((x - s) / 60);
        m = x % 60;
        h = ~~((x - m) / 60);

        return (h ? h + ':' : '') + pad(m) + ':' + pad(s);
    }

    function flash(message, icon, type) {
        var icon = '<i class="glyphicon glyphicon-' + (icon || 'music') + '"></i>';
        $.bootstrapGrowl(icon + ' ' + message, {
            type: type || 'info',
            width: 'auto',
            allow_dismiss: false
        });
    }

    // server uptime
    setInterval((function uptime() {
        var days = parseInt(server.uptime / 86400, 10),
            hours = parseInt(server.uptime / 3600, 10) % 24,
            minutes = parseInt(server.uptime / 60, 10) % 60,
            seconds = parseInt(server.uptime++ % 60, 10);

        $uptime.text(
            (days ? days + ' day' + (days === 1 ? ' ' : 's ') : '') +
            (hours ? hours + ' hour' + (hours === 1 ? ' ' : 's ') : '') +
            (!hours && !minutes ? '' : minutes + ' mins ') +
            (seconds < 10 ? '0' + seconds : seconds) + ' secs');

        return uptime;
    })(), 1e3);

    // login fields focus
    if (!$('#form_login[value=""]').focus().length) {
        $('#form_password').focus();
    }

    // loader
    -function() {
        $document.on({
            ajaxStart: function() {
                $loader.show();
            },
            ajaxStop: function() {
                $loader.hide();
            },
            ajaxError: function(e, xhr) {
                var message = xhr.responseJSON ||
                    'The server is now down. Ask the administrator to restart it.';
                flash(message, 'exclamation-sign', 'danger');
            }
        });

        // set timeout to 10 seconds
        $.ajaxSetup({ timeout: 10000 });

        $('form').on('submit', function() {
            $(':submit', this).addClass('disabled');
            $loader.show();
        });
    }();

    // _main
    $main.length && -function() {
        var $header = $('header small'),
            $playlist = $('.playlist'),
            $focus = $('.playlist-focus'),
            $refresh = $('.playlist-refresh'),
            $shuffle = $('.playlist-shuffle'),
            $position = $('.player-position > input'),
            $volume = $('.player-volume > input'),
            $time = $('.player-time > samp'),
            $prev = $('.player-prev'),
            $play = $('.player-play'),
            $pause = $('.player-pause'),
            $stop = $('.player-stop'),
            $next = $('.player-next'),
            $users = $('.users'),
            $cpu = $('.sys-cpu'),
            $mem = $('.sys-mem'),
            $disk = $('.sys-disk'),
            $total = $('.total-time'),
            current = {},
            roller;

        // list
        function playlist(callback) {
            var $item = function(index, position, song) {
                    return $(
                        '<a data-id="' + song.id + '" data-position="' + position + '" ' +
                            'class="list-group-item' + (song.enabled ? '' : ' disabled') + '">' +
                            '<samp>' + index + '.</samp>&nbsp;' +
                            '<span class="playlist-song">' +
                                '<strong>' + song.artist + '</strong> &mdash; ' +
                                '<span>' + song.title + '</span>' +
                            '</span> ' +
                            '<span class="playlist-info badge">' +
                                ms2time(song.length) +
                            '</span>' +
                        '</a>'
                    );
                };

            $.getJSON('/list').done(function(songs) {
                if (!$.isArray(songs))
                    return;

                var len = (songs.length + '').length,
                    pad = Array(len).join(0),
                    total = 0;

                $playlist.empty();

                $.each(songs, function(i, song) {
                    var index = (pad + (i + 1)).slice(-len);
                    $item(index, i, song).appendTo($playlist);
                    total += song.length;
                });

                if (server.is_admin) {
                    $playlist.children().each(function() {
                        $(
                            '<span class="playlist-toggle btn btn-link btn-xs" title="Enable/disable">' +
                                '<i class="glyphicon glyphicon-flag"></i>' +
                            '</span> ' +
                            '<span class="playlist-edit btn btn-link btn-xs" title="Edit">' +
                                '<i class="glyphicon glyphicon-pencil"></i>' +
                            '</span> ' +
                            '<span class="playlist-after btn btn-link btn-xs" title="Play next">' +
                                '<i class="glyphicon glyphicon-share-alt"></i>' +
                            '</span>'
                        ).appendTo(this);
                    }).hover(function() {
                        $('.btn', this).toggleClass('btn-link btn-default');
                    });
                }

                $total.text(ms2time(total));

                // remove visible tooltips
                $('body > .tooltip').remove();

                // update tooltips
                $('[title]').tooltip({ container: 'body' });

                // popover
                $('.playlist-info', $playlist).popover({
                    container: 'body',
                    trigger: 'click',
                    html: true,
                    title: 'Information',
                    content: function() {
                        var $this = $(this),
                            id = 'popover-' + $.now(),
                            url = '/songs/' + $this.parent().data('id');

                        $.get(url).done(function(song) {
                            $('#' + id).html(
                                '<div><strong>User:</strong> ' + song.user + '</div>' +
                                '<div><strong>Bitrate:</strong> ' + song.bitrate + 'kbps</div>' +
                                '<div><strong>Sample rate:</strong> ' + song.samplerate + 'Hz</div>' +
                                '<div><strong>Created:</strong> ' + song.created + '</div>'
                            );
                        });

                        setTimeout(function() {
                            $this.popover('hide');
                        }, 3000);

                        return '<div id="' + id + '">Loading...</div>';
                    }
                });

                callback();
            });
        }

        // set active
        function set_active(scroll) {
            var $active = $playlist.children().removeClass('active')
                    .filter('[data-id="' + current.id + '"]').addClass('active');

            if ($active.length) {
                var $song = $('.playlist-song', $active),
                    index = +$song.prev('samp').text() + '. ',
                    title = index + $song.text(),
                    text = '      ' + title,
                    i = 0;

                $header.text(title.length > 65
                    ? title.slice(0, 65) + '...' : title);

                clearInterval(roller);
                roller = setInterval(function() {
                    document.title = text.slice(i);
                    if (i++ > text.length - 2) i = 0;
                }, 500);

                scroll && $active[0].scrollIntoView();
            }
        }

        // wso
        function WSO(url) {
            var wso = server.wso,
                socket = new WebSocket(url),
                out = function(cmd) {
                    if (socket.readyState === WebSocket.OPEN) {
                        socket.send(cmd + ':' + [].slice.call(arguments, 1).join('|'));
                    } else {
                        flash('Cannot send command to server', 'exclamation-sign', 'danger');
                    }
                };

            socket.onmessage = function(e) {
                if (!e.data)
                    return;

                var message = e.data.split(':'),
                    cmd = message[0],
                    args = [];

                if (message[1] !== undefined) {
                    args = message[1].split('|');
                }

                switch (+cmd) {
                    case wso._OUT_LIST:
                        playlist(function() {
                            flash('The playlist was updated');
                            set_active(true);
                        });
                        break;
                    case wso._OUT_USERS:
                        $users.children('[data-login]').each(function() {
                            $('.label', this).toggleClass('hidden',
                                $.inArray($(this).data('login'), args) < 0);
                        });
                        break;
                    case wso._OUT_SONG:
                        set_active(current = { id: args[0], length: +args[1] });
                        $position.slider('setAttribute', 'max', current.length);
                        break;
                    case wso._OUT_POSITION:
                        var position = +args[0] || 0;
                        if (!$position.data('drag')) {
                            $position.slider('setValue', position);
                        }
                        $time.text($time.hasClass('inverted')
                            ? '-' + ms2time(current.length - position)
                            : ms2time(position));
                        break;
                    case wso._OUT_VOLUME:
                        if (!$volume.data('drag')) {
                            $volume.slider('setValue', +args[0]);
                        }
                        break;
                    case wso._OUT_NEW:
                        playlist(function() {
                            flash('New song <strong>"' + $('> [data-id="' +
                                args[0] + '"] > .playlist-song', $playlist).text() +
                                '"</strong> was added', null, 'success');
                            set_active();
                        });
                        break;
                    case wso._OUT_MOVE:
                        playlist(function() {
                            flash('Song <strong>"' + $('> [data-id="' +
                                args[0] + '"] > .playlist-song', $playlist).text() +
                                '"</strong> was moved to position ' + ++args[1], 'sort');
                            set_active();
                        });
                        break;
                    case wso._OUT_SHUFFLE:
                        playlist(function() {
                            flash('Playlist was shuffled', 'random');
                            set_active();
                        });
                        break;
                    case wso._OUT_DISK:
                        $disk.text(args[0]);
                        break;
                    case wso._OUT_MEMCPU:
                        $mem.text(args[0] + '%');
                        $cpu.text(args[1] + '%');
                        break;
                    case wso._OUT_TOGGLE:
                        var $item = $('> [data-id="' + args[0] + '"]', $playlist),
                            enabled = !!+args[1];

                        $item.toggleClass('disabled', !enabled);
                        flash('Song <strong>"' + $item.children('.playlist-song').text() +
                            '"</strong> was ' + (enabled ? 'en' : 'dis') + 'abled', 'flag',
                            enabled ? 'success' : 'warning');
                        break;
                    case wso._OUT_AFTER:
                        playlist(function() {
                            flash('Song <strong>"' + $('> [data-id="' +
                                args[0] + '"] > .playlist-song', $playlist).text() +
                                '"</strong> will be played next', 'share-alt');
                            set_active();
                        });
                }
            };

            socket.onclose = function() {
                var interval = setInterval(function() {
                    playlist(function() {
                        WSO('ws://' + location.host + '/wso');
                        clearInterval(interval);
                    });
                }, 15000);

                flash('Connection with server was closed. Trying to reconnect in 15 seconds...', 'exclamation-sign', 'danger');
            };

            socket.onerror = function() {
                flash('Stream error identified, please reload the page', 'exclamation-sign', 'danger');
                socket.close();
            };

            $focus.on('click', function() {
                var $active = $('.playlist > .active');
                $active.length && $active[0].scrollIntoView();
            });

            $refresh.on('click', function() {
                playlist(function() {
                    set_active(true);
                });
            });

            if (!server.is_admin)
                return;

            // admin controls
            $prev.on('click', function() {
                out(wso._IN_PREV);
            });

            $play.on('click', function() {
                out(wso._IN_PLAY);
            });

            $pause.on('click', function() {
                out(wso._IN_PAUSE);
            });

            $stop.on('click', function() {
                out(wso._IN_STOP);
            });

            $next.on('click', function() {
                out(wso._IN_NEXT);
            });

            $position.on('slideStop', function(e) {
                out(wso._IN_POSITION, e.value);
            });

            $volume.on('slideStop', function(e) {
                out(wso._IN_VOLUME, e.value);
            });

            $playlist.on('click', '> [data-id]', function() {
                out(wso._IN_SONG, $(this).data('id'));
            });

            $playlist.on('click', '.playlist-toggle', function() {
                out(wso._IN_TOGGLE, $(this.parentNode).data('id'));
                return false;
            });

            $playlist.on('click', '.playlist-after', function() {
                out(wso._IN_AFTER, $(this.parentNode).data('id'));
                return false;
            });

            $shuffle.on('click', function() {
                out(wso._IN_SHUFFLE);
            });

            new Sortable($playlist[0], {
                onUpdate: function(e) {
                    var $item = $(e.item),
                        index = $item.index();

                    if (index !== $item.data('position')) {
                        out(wso._IN_MOVE, $item.data('id'), index);
                    }
                }
            });
        }

        // position slider
        $position.slider({
            value: 0,
            enabled: server.is_admin,
            formater: function(value) {
                return ms2time(value);
            }
        }).on({
            slideStart: function() {
                $(this).data('drag', true);
            },
            slideStop: function() {
                $(this).data('drag', false);
            }
        });

        // volume slider
        $volume.slider({
            min: 50,
            max: 100,
            value: 80,
            enabled: server.is_admin,
            formater: function(value) {
                return 'Volume: ' + value + '%';
            }
        }).on({
            slideStart: function() {
                $(this).data('drag', true);
            },
            slideStop: function() {
                $(this).data('drag', false);
            }
        });

        // time
        $time.on('click', function() {
            $(this).toggleClass('inverted').text('--:--');
        });

        // permissions
        $('.player .btn').toggleClass('disabled', !server.is_admin);

        // init
        playlist(function() {
            var $header = $playlist.prev('.panel-heading'),
                $footer = $playlist.next('.panel-footer'),
                $upanel = $users.closest('.panel'),
                offset = 25;

            $window.on('resize', (function resize() {
                var top = $playlist.offset().top,
                    header = $header.outerHeight(),
                    footer = $footer.outerHeight(),
                    height_left = $window.height() - top - footer - offset,
                    height_right = $upanel.height() - header - footer;

                $playlist.css('max-height', Math.max(height_left, height_right));
                return resize;
            })());

            WSO('ws://' + location.host + '/wso');
        });

        // playlist edit
        $playlist.on('click', '.playlist-edit', function() {
            location.href = '/songs/' + $(this).parent().data('id');
            return false;
        });

        // playlist info
        $playlist.on('click', '.playlist-info', function() {
            return false;
        });
    }();

    // _upload
    $upload.length && -function() {
        $('.upload-add').on('click', function() {
            var $items = $('.upload-item'),
                len = $items.length;

            $('.upload-remove', $items).removeClass('hidden').end().eq(0).clone()
                .find('.upload-index').text($items.length + 1).end()
                .find(':input').val('').end()
                .appendTo('.upload-container');

            (len === 8) && $(this).addClass('disabled');
        });

        $('.upload-container').on('click', '.upload-remove', function() {
            $(this).closest('.upload-item').remove();

            $('.upload-index').text(function(i) {
                return i + 1;
            });

            if ($('.upload-item').length < 2) {
                $('.upload-remove').addClass('hidden');
            }
        });
    }();
}();
