/**
 * CASTÚO-SYSTEM™ v3.1 — Form JS
 * Envía el formulario al proxy WP REST y renderiza el resultado.
 * Sin dependencias externas excepto jQuery (incluido en WP).
 */
/* global castuo, jQuery */
(function ($) {
    'use strict';

    const HISTORY_KEY = 'castuo_lote_history';
    const MAX_HISTORY = 20;

    // ── Historial en localStorage ─────────────────────────────────────────────
    function loadHistory() {
        try {
            return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
        } catch { return []; }
    }

    function saveHistory(item) {
        const hist = loadHistory();
        hist.unshift(item);
        localStorage.setItem(HISTORY_KEY, JSON.stringify(hist.slice(0, MAX_HISTORY)));
        renderHistory();
    }

    function renderHistory() {
        const hist = loadHistory();
        const $el = $('#castuo-history-table');
        if (!hist.length) {
            $el.html('<p>' + (castuo.i18n?.noHistory || 'Sin lotes validados aún.') + '</p>');
            return;
        }
        let rows = hist.map(function (item) {
            const shortHash = (item.tx_hash || '').substring(0, 20) + '…';
            const badge = item.status === 'OK'
                ? '<span class="castuo-badge castuo-badge--ok">GaiaChain</span>'
                : '<span class="castuo-badge castuo-badge--sim">Simulado</span>';
            return '<tr>' +
                '<td>' + $('<span>').text(item.lote_id).html() + '</td>' +
                '<td><code title="' + $('<span>').text(item.tx_hash).html() + '">' + shortHash + '</code></td>' +
                '<td>' + badge + '</td>' +
                '<td>' + $('<span>').text((item.generado_en || '').replace('T', ' ').substring(0, 19)).html() + '</td>' +
                '</tr>';
        }).join('');

        $el.html(
            '<table class="castuo-history__table">' +
            '<thead><tr><th>Lote</th><th>TX Hash</th><th>Blockchain</th><th>Fecha</th></tr></thead>' +
            '<tbody>' + rows + '</tbody>' +
            '</table>'
        );
    }

    // ── Submit ────────────────────────────────────────────────────────────────
    $(document).ready(function () {
        renderHistory();

        $('#castuo-form').on('submit', function (e) {
            e.preventDefault();

            // Validación básica
            const loteId = $.trim($('#castuo-lote-id').val());
            if (loteId.length < 3) {
                showError('El ID de lote debe tener al menos 3 caracteres.');
                return;
            }
            const fechaCosecha = $('#castuo-fecha').val();
            if (!fechaCosecha) {
                showError('La fecha de cosecha es obligatoria.');
                return;
            }

            // Construir metadatos
            const metadatos = {
                cultivo:       $('#castuo-cultivo').val()   || undefined,
                humedad_pct:   parseFloat($('#castuo-humedad').val()) || undefined,
                thc_pct:       parseFloat($('#castuo-thc').val())     || undefined,
                cbd_pct:       parseFloat($('#castuo-cbd').val())      || undefined,
                kg_cosechados: parseFloat($('#castuo-kg').val())       || undefined,
                fecha_cosecha: fechaCosecha,
                ubicacion:     $('#castuo-ubicacion').val()            || undefined,
                eco:           $('#castuo-eco').is(':checked'),
                aemps_expediente: $('#castuo-expediente').val()        || undefined,
            };
            // Limpiar undefined
            Object.keys(metadatos).forEach(function (k) {
                if (metadatos[k] === undefined) delete metadatos[k];
            });

            // UI: estado cargando
            setLoading(true);
            hideResult();
            hideError();

            $.ajax({
                url:         castuo.restUrl,
                method:      'POST',
                contentType: 'application/json',
                data:        JSON.stringify({ lote_id: loteId, metadatos: metadatos }),
                beforeSend:  function (xhr) {
                    xhr.setRequestHeader('X-WP-Nonce', castuo.nonce);
                },
                success: function (data) {
                    setLoading(false);
                    showResult(data);
                    saveHistory(data);
                },
                error: function (xhr) {
                    setLoading(false);
                    const detail = (xhr.responseJSON && xhr.responseJSON.message)
                        ? xhr.responseJSON.message
                        : ('HTTP ' + xhr.status + ': ' + xhr.statusText);
                    showError(detail);
                },
            });
        });
    });

    // ── Helpers UI ────────────────────────────────────────────────────────────
    function setLoading(on) {
        const $btn    = $('#castuo-submit');
        const $label  = $btn.find('.castuo-btn__label');
        const $spinner= $btn.find('.castuo-btn__spinner');
        $btn.prop('disabled', on);
        $label.toggle(!on);
        $spinner.toggle(on);
    }

    function showResult(data) {
        const isOK = data.status === 'OK';
        $('#castuo-result').removeAttr('hidden').show();
        $('.castuo-result__status--ok').toggle(isOK);
        $('.castuo-result__status--fallback').toggle(!isOK);

        $('#r-lote-id').text(data.lote_id || '');
        $('#r-tx-hash code').text(data.tx_hash || '');
        $('#r-blockchain').text(data.blockchain || '');
        $('#r-fecha').text((data.generado_en || '').replace('T', ' ').substring(0, 19));

        // Cert link — solo si la ruta empieza por /tmp o /data (en contenedor)
        if (data.certificado_path) {
            const certUrl = castuo.homeUrl + '/castuo-cert/?path=' + encodeURIComponent(data.certificado_path);
            $('#r-cert-link').attr('href', certUrl).removeAttr('hidden');
        }
        if (data.qr_path) {
            const qrUrl = castuo.homeUrl + '/castuo-qr/?path=' + encodeURIComponent(data.qr_path);
            $('#r-qr-link').attr('href', qrUrl).removeAttr('hidden');
        }
    }

    function hideResult() {
        $('#castuo-result').attr('hidden', true).hide();
    }

    function showError(msg) {
        $('#castuo-error').removeAttr('hidden').text('❌ ' + msg);
    }

    function hideError() {
        $('#castuo-error').attr('hidden', true).text('');
    }

}(jQuery));
