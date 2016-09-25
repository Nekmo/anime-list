/**
 * Created by nekmo on 24/09/16.
 */

var animes = [];
var fuse = null;

function getAnimes(){
    if(animes.length){
        return animes;
    }
    $('.anime', $('#animes')).each(function (i, anime) {
        var title = $('.title', anime).text();
        animes.push({title: title, element: anime});
    });

    return animes;
}


function getFuse(){
    // if(fuse){
    //     return fuse;
    // }
    return new Fuse(getAnimes(), { keys: ["title"] });
}


$('.synopsis').hover(function(){
    var title = $(this).parent().children('.title')[0];
    if($(title).height() > 50){
        $(this).height(130);
    }
    $(this).perfectScrollbar();
});


function search(){
    var query = $('#search').val();
    var results = getFuse().search(query);
    var $results = $('#results');
    var $animes = $('#animes');
    $results[0].innerHTML = '';
    if(!query){
        $animes.show();
        return
    }
    $animes.hide();
    results = results.slice(0, 12);
    $.each(results, function (i, item) {
        $results.append(item['element']);
    })
}


$('#search').keyup(function() {
  clearTimeout($.data(this, 'timer'));
  var wait = setTimeout(search, 500);
  $(this).data('timer', wait);
});

