'use strict;'

// Main.
const SZ = 512;
var data = null;  // Global for debugging.
$(document).ready(function() {
    // Show dataset name.
    fetch('title.txt').then((response) => response.text().then((text) => {
        document.title = `${text} - datasetter`;
        $('#ds_name').text(text);
    }));

    // Load data.
    fetch('data.json').then((response) => response.json().then((json) => {
        data = json;
        $('#ds_size').text(Object.keys(data).length);
        const mode = new URLSearchParams(window.location.search).get('mode');
        if (mode == 'crop') {
            crop();
        } else if (mode == 'rotate') {
            rotate();
        } else {
            caption();
        }
    }));
});

// ---

function get_id_from_url() {
    let s = new URLSearchParams(window.location.search);
    let id = s.get('id');
    if (!id) return 0;
    return parseInt(id);
}

function go_to_id(id) {
    if (id < 0) return;
    if (id >= Object.keys(data).length) return;
    let s = new URLSearchParams(window.location.search);
    s.set('id', id);
    window.location.search = '?' + s.toString();
}

var current_id = null;
function caption() {
    $('#content').html('Caption:<br>');
    $('#mode_caption').attr('class', 'mode_select');
    for (const [n, obj] of Object.entries(data)) {
        if (!obj.caption && !obj.skip) {
            current_id = n;
            $('<img />', {class: 'thumbnail', src: `thumbnail/${n}/${SZ}`})
                .appendTo($('#content'));
            $('<br/>').appendTo($('#content'));
            let txt = $(
                '<textarea placeholder="enter caption, hit enter to save\nhit ctrl-s to mark as skipped"></textarea>');
            txt.appendTo($('#content'));
            txt.focus();
            txt.keypress(function(ev) {
                if (ev.which == 13) {
                    ev.preventDefault();
                    obj.caption = txt.val();
                    $.post(
                        'update',
                        JSON.stringify({'id': n, 'caption': txt.val()}));
                    caption();
                }
            });
            break;
        }
    }

    // Bind keys.
    $(window).bind('keydown', function(event) {
        var key = String.fromCharCode(event.which).toLowerCase();
        if (key == 's' && (event.ctrlKey || event.metaKey)) {
            event.preventDefault();
            data[current_id].skip = true;
            $.post('update', JSON.stringify({'id': current_id, 'skip': true}));
            caption();
        }
    });
}

function crop() {
    const sz = 256;  // Preview size.
    $('#mode_crop').attr('class', 'mode_select');
    const id = get_id_from_url();
    const md = data[id];
    let content = $('#content').html('');
    $('<div>')
        .text(`Crop: ${id + 1} / ${Object.keys(data).length} (n = ${md.n}) |
    original size ${md.orig_w} x ${md.orig_h}`)
        .appendTo(content);

    function make_preview(key, x, y, wh, txt) {
        let out = $('<div style="float:left; margin:5px;">');
        let img = $('<img />', {
                      class: 'thumbnail',
                      width: sz,
                      height: sz,
                      style: 'cursor:pointer',
                      src: `crop/${id}/${x}/${y}/${wh}/${sz}`
                  })
                      .attr('id', `click${key}`)
                      .appendTo(out);
        $('<div>').text(txt).appendTo(out);

        img.click(() => $.post('update', JSON.stringify({
                             'id': md.n,
                             'manual_crop': 1,
                             'x': x,
                             'y': y,
                             'w': wh,
                             'h': wh,
                         })).then(() => go_to_id(id + 1)));
        return out;
    }

    if (md.orig_w > md.orig_h) {
        // Landscape mode.
        let wh = md.orig_h;
        let m = ((md.orig_w - wh) / 2) >> 0;
        let r = md.orig_w - wh;
        make_preview(1, 0, 0, wh, '1: Left').appendTo(content);
        make_preview(2, m, 0, wh, '2: Center').appendTo(content);
        make_preview(3, r, 0, wh, '3: Right').appendTo(content);
    } else {
        // Portrait mode.
        let wh = md.orig_w;
        let mid = ((md.orig_h - wh) / 2) >> 0;
        let btm = md.orig_h - wh;
        make_preview(1, 0, 0, wh, '1: Top').appendTo(content);
        make_preview(2, 0, mid, wh, '2: Middle').appendTo(content);
        make_preview(3, 0, btm, wh, '3: Bottom').appendTo(content);
    }

    $('<div style="clear:both">').appendTo(content);
    if (md.manual_crop) {
        $('<p class="warn">ALREADY MANUALLY CROPPED</p>').appendTo(content);
    }
    $('<p>').appendTo(content);
    $('<div>')
        .text(
            `Press or click 1/2/3 to choose a crop and move on to the next image.`)
        .appendTo(content);
    $('<div>')
        .text(`Press S to mark the image as skipped and move on.`)
        .appendTo(content);
    $('<div>')
        .text(`Press A or D to move to the prev/next image without saving.`)
        .appendTo(content);
    $('<pre>').text(JSON.stringify(md, null, 2)).appendTo(content);

    // Bind keys.
    $(window).bind('keydown', function(event) {
        var key = String.fromCharCode(event.which).toLowerCase();
        if (key == 'a') {
            go_to_id(id - 1);
        }
        if (key == 'd') {
            go_to_id(id + 1);
        }
        if (key == '1' || key == '2' || key == '3') {
            $(`#click${key}`).click();
        }
        if (key == 's') {
            $.post('update', JSON.stringify({
                 'id': md.n,
                 'skip': 'during manual crop',
             })).then(() => go_to_id(id + 1));
        }
    });
}

function rotate() {
    const sz = 256;  // Preview size.
    $('#mode_rotate').attr('class', 'mode_select');
    const id = get_id_from_url();
    const md = data[id];
    let content = $('#content').html('');
    $('<div>')
        .text(`Rotate: ${id + 1} / ${Object.keys(data).length} (n = ${md.n})`)
        .appendTo(content);

    function make_preview(key, rot) {
        let out = $('<div style="float:left; margin:5px;">');
        let img = $('<img />', {
                      class: 'thumbnail',
                      width: sz,
                      height: sz,
                      style: 'cursor:pointer',
                      src: `rotate/${id}/${rot}/${sz}`
                  })
                      .attr('id', `click${key}`)
                      .appendTo(out);
        $('<div>').text(`Press ${key}`).appendTo(out);

        img.click(() => $.post('update', JSON.stringify({
                             'id': md.n,
                             'manual_rot': 1,
                             'rot': rot,
                         })).then(() => go_to_id(id + 1)));
        return out;
    }

    make_preview('1', 1).appendTo(content);
    make_preview('2', 0).appendTo(content);
    make_preview('3', 3).appendTo(content);
    make_preview('4', 2).appendTo(content);

    $('<div style="clear:both">').appendTo(content);
    if (md.manual_rot) {
        $('<p class="warn">ALREADY MANUALLY ROTATED</p>').appendTo(content);
    }
    $('<p>').appendTo(content);
    $('<div>')
        .text(
            `Press or click 1/2/3/4 to choose a rotation and move on to the next image.`)
        .appendTo(content);
    // TODO: factor this:
    $('<div>')
        .text(`Press S to mark the image as skipped and move on.`)
        .appendTo(content);
    $('<div>')
        .text(`Press A or D to move to the prev/next image without saving.`)
        .appendTo(content);
    $('<pre>').text(JSON.stringify(md, null, 2)).appendTo(content);

    // Bind keys.
    $(window).bind('keydown', function(event) {
        var key = String.fromCharCode(event.which).toLowerCase();
        if (key == '1' || key == '2' || key == '3' || key == '4') {
            $(`#click${key}`).click();
        }
        // TODO: factor the rest of this:
        if (key == 'a') {
            go_to_id(id - 1);
        }
        if (key == 'd') {
            go_to_id(id + 1);
        }
        if (key == 's') {
            $.post('update', JSON.stringify({
                 'id': md.n,
                 'skip': 'during manual rotation',
             })).then(() => go_to_id(id + 1));
        }
    });
}
