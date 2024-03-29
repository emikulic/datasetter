'use strict;'

// Get ID from URL.
const curr_id = (() => {
    let s = new URLSearchParams(window.location.search);
    let i = s.get('id');
    if (!i) return 0;
    return parseInt(i);
})();

const SZ = 512;
var data = null;  // Global for debugging.

// Main.
$(document).ready(function() {
    // Show dataset name.
    fetch('title.txt').then((response) => response.text().then((text) => {
        document.title = `${text} - datasetter`;
        $('#ds_name').text(text);
    }));

    // Fill in mode links.
    let s = new URLSearchParams(window.location.search);
    for (let mode of ['catalog', 'caption', 'crop', 'rotate']) {
        s.set('mode', mode);
        $(`#mode_${mode}`).attr('href', '?' + s.toString());
    }

    // Load data.
    fetch('data.json').then((response) => response.json().then((json) => {
        data = json;
        $('#ds_size').text(Object.keys(data).length);

        let num_caption = 0;
        let num_crop = 0;
        let num_rotate = 0;
        let num_skip = 0;
        for (const [n, md] of Object.entries(data)) {
            if ('caption' in md) {
                num_caption++;
            }
            if ('manual_crop' in md) {
                num_crop++;
            }
            if ('manual_rot' in md) {
                num_rotate++;
            }
            if ('skip' in md) {
                num_skip++;
            }
        }
        $('#num_caption').text(num_caption);
        $('#num_crop').text(num_crop);
        $('#num_rotate').text(num_rotate);
        $('#num_skip').text(num_skip);

        const mode = new URLSearchParams(window.location.search).get('mode');
        if (mode == 'catalog') {
            catalog();
        } else if (mode == 'crop') {
            crop();
        } else if (mode == 'rotate') {
            rotate();
        } else {
            caption();
        }
    }));
});

// ---

function go_to_id(id) {
    if (id < 0) return;
    if (id >= Object.keys(data).length) return;
    let s = new URLSearchParams(window.location.search);
    s.set('id', id);
    window.location.search = '?' + s.toString();
}

function go_to_mode(mode) {
    let s = new URLSearchParams(window.location.search);
    s.set('mode', mode);
    window.location.search = '?' + s.toString();
}

function append_warns(md, content) {
    if (md.manual_crop) {
        $('<p class="warn">ALREADY MANUALLY CROPPED</p>').appendTo(content);
    }
    if (md.skip) {
        $('<p class="warn">ALREADY SKIPPED</p>').appendTo(content);
    }
    if (md.manual_rot) {
        $('<p class="warn">ALREADY MANUALLY ROTATED</p>').appendTo(content);
    }
}

function catalog() {
    const sz = 256;  // Preview size.
    let content = $('#content').html('Catalog:<br>');
    for (const [n, md] of Object.entries(data)) {
        let a = $('<a>').attr('href', `?mode=caption&id=${n}`);
        // Trade-off: load full size thumbnails to hit the cache, but then scale
        // them down in the browser.
        let img = $('<img>', {
                      style: 'float:left; margin:5px;',
                      loading: 'lazy',
                      class: 'thumbnail',
                      src: `masked_thumbnail/${n}/${SZ}`
                  })
                      .width(sz)
                      .height(sz)
                      .appendTo(a);
        if (md.skip) {
            // Fade skipped images.
            img.css('opacity', 0.3);
            img.css('border', '2px solid #0ff');
            img.css('margin', '3px');
        }
        if (n == curr_id) {
            // Highlight selected image.
            img.css('border', '2px solid red');
            img.css('margin', '3px');
            // TODO: img[0].scrollIntoView(); (doesn't work)
        }
        a.appendTo(content);
    }
}

function caption() {
    const md = data[curr_id];
    let content = $('#content').html('');
    $('<div>')
        .text(`Caption: ${curr_id + 1} / ${Object.keys(data).length} (n = ${
            md.n})`)
        .appendTo(content);
    $('#mode_caption').attr('class', 'mode_select');
    $('<img>', {class: 'thumbnail', src: `thumbnail/${curr_id}/${SZ}`})
        .width(SZ)
        .height(SZ)
        .appendTo(content);
    let has_mask = false;
    if ('mask_state' in md && md['mask_state'] == 'done') {
        has_mask = true;
    }
    if (has_mask) {
        let mask_img =
            $('<img>',
              {class: 'thumbnail', src: `mask_thumbnail/${curr_id}/${SZ}`})
                .width(SZ)
                .height(SZ)
                .appendTo(content);
        mask_img.css('margin-left', '5px');
    }
    $('<br>').appendTo(content);
    let txt =
        $('<textarea placeholder="enter caption, hit enter to save\nhit ctrl-s to mark as skipped"></textarea>')
            .appendTo(content);
    txt.focus();
    txt.keypress(function(ev) {
        if (ev.which == 13) {
            ev.preventDefault();
            $.post('update', JSON.stringify({
                 'id': curr_id,
                 'caption': txt.val()
             })).then(() => go_to_id(curr_id + 1));
        }
    });
    $('<br>').appendTo(content);

    let prep_mask =
        $('<button type="button">Prepare mask</button>').appendTo(content);
    if ('mask_fn' in md) {
        if (has_mask) {
            prep_mask.text('(mask is already present)');
        } else {
            prep_mask.text(
                '(mask is being prepared, run apply_masks.py when done)');
        }
        prep_mask.prop('disabled', true);
    }
    prep_mask.click(function(ev) {
        $.post('prep_mask', JSON.stringify({
             'id': curr_id
         })).then(() => prep_mask.prop('disabled', true));
    });

    if (has_mask) {
        let redo_mask =
            $('<button type="button">Redo mask</button>').appendTo(content);
        redo_mask.click(function(ev) {
            $.post('prep_mask', JSON.stringify({
                'id': curr_id,
                'force': 1
            })).then(() => redo_mask.prop('disabled', true));
        });
    }

    append_warns(md, content);
    if ('caption' in md) {
        txt.val(md['caption']);
    } else if ('autocaption' in md) {
        let ac = md['autocaption'];
        if (typeof (ac) !== 'string') {
            ac = ac[0][1];  // First string in autocaptions.
        }
        txt.val(ac);
        $('<p class="warn">USING AUTOCAPTION</p>').appendTo(content);
    }
    $('<div>')
        .text(
            `Press PageUp or PageDown to move to the prev/next image without saving.`)
        .appendTo(content);
    $('<pre>').text(JSON.stringify(md, null, 2)).appendTo(content);

    // Bind keys.
    $(window).bind('keydown', function(event) {
        if (event.which == 33) {  // PageUp
            go_to_id(curr_id - 1);
        } else if (event.which == 34) {  // PageDown
            go_to_id(curr_id + 1);
        }
        var key = String.fromCharCode(event.which).toLowerCase();
        if (key == 's' && (event.ctrlKey || event.metaKey)) {
            event.preventDefault();
            $.post('update', JSON.stringify({
                 'id': curr_id,
                 'skip': 'during captioning'
             })).then(() => go_to_id(curr_id + 1));
        }
    });
}

function crop() {
    const sz = 256;  // Preview size.
    $('#mode_crop').attr('class', 'mode_select');
    const md = data[curr_id];
    let content = $('#content').html('');
    $('<div>')
        .text(
            `Crop: ${curr_id + 1} / ${Object.keys(data).length} (n = ${md.n}) |
    original size ${md.orig_w} x ${md.orig_h}`)
        .appendTo(content);

    function make_preview(key, x, y, wh, txt) {
        let out = $('<div style="float:left; margin:5px;">');
        let img = $('<img />', {
                      class: 'thumbnail',
                      style: 'cursor:pointer',
                      src: `crop/${curr_id}/${x}/${y}/${wh}/${sz}`
                  })
                      .width(sz)
                      .height(sz)
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
                         })).then(() => go_to_id(curr_id + 1)));
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
    append_warns(md, content);
    $('<p>').appendTo(content);
    $('<div>')
        .text(
            `Press or click 1/2/3 to choose a crop and move on to the next image.`)
        .appendTo(content);
    $('<div>')
        .text(`Press W to mark the image as not skipped and move on.`)
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
            go_to_id(curr_id - 1);
        }
        if (key == 'd') {
            go_to_id(curr_id + 1);
        }
        if (key == '1' || key == '2' || key == '3') {
            $(`#click${key}`).click();
        }
        if (key == 's') {
            $.post('update', JSON.stringify({
                 'id': md.n,
                 'skip': 'during manual crop',
             })).then(() => go_to_id(curr_id + 1));
        }
        if (key == 'w') {
            $.post('update', JSON.stringify({
                 'id': md.n,
                 'unskip': 1,
             })).then(() => go_to_id(curr_id + 1));
        }
    });
}

function rotate() {
    const sz = 256;  // Preview size.
    $('#mode_rotate').attr('class', 'mode_select');
    const md = data[curr_id];
    let content = $('#content').html('');
    $('<div>')
        .text(`Rotate: ${curr_id + 1} / ${Object.keys(data).length} (n = ${
            md.n})`)
        .appendTo(content);

    function make_preview(key, rot) {
        let out = $('<div style="float:left; margin:5px;">');
        let img = $('<img />', {
                      class: 'thumbnail',
                      width: sz,
                      height: sz,
                      style: 'cursor:pointer',
                      src: `rotate/${curr_id}/${rot}/${sz}`
                  })
                      .attr('id', `click${key}`)
                      .appendTo(out);
        $('<div>').text(`Press ${key}`).appendTo(out);

        img.click(() => $.post('update', JSON.stringify({
                             'id': md.n,
                             'manual_rot': 1,
                             'rot': rot,
                         })).then(() => go_to_id(curr_id + 1)));
        return out;
    }

    make_preview('1', 1).appendTo(content);
    make_preview('2', 0).appendTo(content);
    make_preview('3', 3).appendTo(content);
    make_preview('4', 2).appendTo(content);

    $('<div style="clear:both">').appendTo(content);
    append_warns(md, content);
    $('<p>').appendTo(content);
    $('<div>')
        .text(
            `Press or click 1/2/3/4 to choose a rotation and move on to the next image.`)
        .appendTo(content);
    // TODO: factor this:
    $('<div>')
        .text(`Press W to mark the image as not skipped and move on.`)
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
        if (key == '1' || key == '2' || key == '3' || key == '4') {
            $(`#click${key}`).click();
        }
        // TODO: factor the rest of this:
        if (key == 'a') {
            go_to_id(curr_id - 1);
        }
        if (key == 'd') {
            go_to_id(curr_id + 1);
        }
        if (key == 's') {
            $.post('update', JSON.stringify({
                 'id': md.n,
                 'skip': 'during manual rotation',
             })).then(() => go_to_id(curr_id + 1));
        }
        if (key == 'w') {
            $.post('update', JSON.stringify({
                 'id': md.n,
                 'unskip': 1,
             })).then(() => go_to_id(curr_id + 1));
        }
    });
}
