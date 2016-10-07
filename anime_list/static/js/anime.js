/**
 * Created by nekmo on 25/09/16.
 */
$('.player').on('click', function (ev) {
    console.debug(ev.currentTarget);
    var $element = $(ev.currentTarget);
    var $ul = $element.closest('ul');
    var player_id = $element.data('player_id');
    var file = $ul.data('file');
    var anime = $ul.data('anime');
    $.post('/play', {file: file, player_id: player_id, anime: anime});
});