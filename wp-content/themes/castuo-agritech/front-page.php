<?php
/**
 * Front page — Home B2B landing
 */
get_header();

$tagline  = get_theme_mod('castuo_hero_tagline',  'Agricultura inteligente.<br><em>Trazabilidad verificable.</em>');
$subtitle = get_theme_mod('castuo_hero_subtitle',  'Microgreens, brotes y flores comestibles cultivados en invernadero agrovoltaico hidropónico. Cada lote trazado en blockchain desde la semilla hasta tu almacén.');
$cta_text = get_theme_mod('castuo_cta_text',       'Solicitar catálogo B2B');
$cta_url  = get_theme_mod('castuo_cta_url',        '#contacto');
$email    = get_theme_mod('castuo_contact_email',  'b2b@castuo360.eu');
$moq_note = get_theme_mod('castuo_moq_note',       'Pedido mínimo 5 kg/variedad. Entrega en cadena de frío 2-8 °C.');
?>

<main id="main" role="main">

  <!-- ═══ HERO ════════════════════════════════════════════════ -->
  <section class="hero" aria-labelledby="hero-heading">
    <div class="hero-bg" aria-hidden="true"></div>
    <div class="hero-pattern" aria-hidden="true"></div>
    <div class="container">
      <div class="hero-content">

        <div class="hero-badge" aria-label="Estado operativo">
          <span class="dot" aria-hidden="true"></span>
          <?php esc_html_e('Sistema activo · EU Sovereign · RGPD', 'castuo-agritech'); ?>
        </div>

        <h1 id="hero-heading"><?php echo wp_kses_post($tagline); ?></h1>

        <p><?php echo esc_html($subtitle); ?></p>

        <div class="hero-actions">
          <a href="<?php echo esc_url($cta_url); ?>" class="btn btn-primary">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M20 12V22H4V12"/><path d="M22 7H2v5h20V7z"/><path d="M12 22V7"/><path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z"/><path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z"/></svg>
            <?php echo esc_html($cta_text); ?>
          </a>
          <a href="<?php echo esc_url(home_url('/verificar/')); ?>" class="btn btn-outline">
            <?php esc_html_e('Verificar trazabilidad', 'castuo-agritech'); ?>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><polyline points="9 18 15 12 9 6"/></svg>
          </a>
        </div>

        <div class="hero-trust" role="list">
          <div class="trust-item" role="listitem">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            <?php esc_html_e('GaiaChain 3.0 · PoA blockchain EU', 'castuo-agritech'); ?>
          </div>
          <div class="trust-item" role="listitem">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            <?php esc_html_e('IPFS inmutable · 3 réplicas EU', 'castuo-agritech'); ?>
          </div>
          <div class="trust-item" role="listitem">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>
            <?php esc_html_e('RGPD · AI Act · eIDAS', 'castuo-agritech'); ?>
          </div>
          <div class="trust-item" role="listitem">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>
            <?php esc_html_e('Energía solar agrovoltaica', 'castuo-agritech'); ?>
          </div>
        </div>

      </div>
    </div>
  </section>


  <!-- ═══ PRODUCTS ═══════════════════════════════════════════ -->
  <section class="section products-section" id="productos" aria-labelledby="products-heading">
    <div class="container">

      <div class="section-header">
        <span class="section-label"><?php esc_html_e('Catálogo B2B', 'castuo-agritech'); ?></span>
        <h2 id="products-heading"><?php esc_html_e('Productos con trazabilidad completa', 'castuo-agritech'); ?></h2>
        <p><?php esc_html_e('Cada lote disponible en tu panel con pH medio, CE, origen parcelario SIGPAC y certificado TRACES. Blockchain-verified, sin intermediarios.', 'castuo-agritech'); ?></p>
      </div>

      <div class="products-grid">

        <!-- Microgreens -->
        <article class="product-card" aria-label="<?php esc_attr_e('Microgreens', 'castuo-agritech'); ?>">
          <div class="product-visual" data-product="microgreens">
            <div class="product-visual-inner" aria-hidden="true">🌱</div>
            <div class="product-chain-badge" aria-label="<?php esc_attr_e('Verificado en blockchain', 'castuo-agritech'); ?>">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              <?php esc_html_e('On-chain', 'castuo-agritech'); ?>
            </div>
          </div>
          <div class="product-body">
            <div class="product-category"><?php esc_html_e('Alta densidad nutricional', 'castuo-agritech'); ?></div>
            <h3><?php esc_html_e('Microgreens', 'castuo-agritech'); ?></h3>
            <p class="product-desc"><?php esc_html_e('Girasol, rábano, guisante, brócoli, albahaca. Cosechados 8-14 días. pH medio controlado 5.8-6.2. CE 1.4-1.8 mS/cm. Disponibles semanalmente.', 'castuo-agritech'); ?></p>
            <div class="product-specs" aria-label="<?php esc_attr_e('Especificaciones', 'castuo-agritech'); ?>">
              <span class="spec-tag">pH 5.8–6.2</span>
              <span class="spec-tag">CE 1.4–1.8</span>
              <span class="spec-tag">Hidropónico</span>
              <span class="spec-tag">Sin pesticidas</span>
              <span class="spec-tag">Solar &gt;60%</span>
            </div>
            <div class="product-footer">
              <div class="product-moq">
                <strong><?php esc_html_e('Desde 2 kg/var', 'castuo-agritech'); ?></strong><br>
                <span><?php esc_html_e('Caja 1 kg disponible', 'castuo-agritech'); ?></span>
              </div>
              <a href="<?php echo esc_url($cta_url); ?>" class="btn-product">
                <?php esc_html_e('Pedir muestra', 'castuo-agritech'); ?>
              </a>
            </div>
          </div>
        </article>

        <!-- Brotes -->
        <article class="product-card" aria-label="<?php esc_attr_e('Brotes', 'castuo-agritech'); ?>">
          <div class="product-visual" data-product="brotes">
            <div class="product-visual-inner" aria-hidden="true">🌿</div>
            <div class="product-chain-badge">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              <?php esc_html_e('On-chain', 'castuo-agritech'); ?>
            </div>
          </div>
          <div class="product-body">
            <div class="product-category"><?php esc_html_e('Germinados premium', 'castuo-agritech'); ?></div>
            <h3><?php esc_html_e('Brotes', 'castuo-agritech'); ?></h3>
            <p class="product-desc"><?php esc_html_e('Alfalfa, lentejas, mung, trigo. Ciclo 3-6 días en húmedo. Trazabilidad desde semilla certificada REGEPA. Envase modificado 200-500 g.', 'castuo-agritech'); ?></p>
            <div class="product-specs">
              <span class="spec-tag">Húmedo controlado</span>
              <span class="spec-tag">O₂ &gt;6 mg/L</span>
              <span class="spec-tag">REGEPA</span>
              <span class="spec-tag">Sem. ecológica</span>
            </div>
            <div class="product-footer">
              <div class="product-moq">
                <strong><?php esc_html_e('Desde 5 kg/semana', 'castuo-agritech'); ?></strong><br>
                <span><?php esc_html_e('Formatos 200 g – 2 kg', 'castuo-agritech'); ?></span>
              </div>
              <a href="<?php echo esc_url($cta_url); ?>" class="btn-product">
                <?php esc_html_e('Pedir muestra', 'castuo-agritech'); ?>
              </a>
            </div>
          </div>
        </article>

        <!-- Flores comestibles -->
        <article class="product-card" aria-label="<?php esc_attr_e('Flores comestibles', 'castuo-agritech'); ?>">
          <div class="product-visual" data-product="flores">
            <div class="product-visual-inner" aria-hidden="true">🌸</div>
            <div class="product-chain-badge">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              <?php esc_html_e('On-chain', 'castuo-agritech'); ?>
            </div>
          </div>
          <div class="product-body">
            <div class="product-category"><?php esc_html_e('Alta gastronomía', 'castuo-agritech'); ?></div>
            <h3><?php esc_html_e('Flores comestibles', 'castuo-agritech'); ?></h3>
            <p class="product-desc"><?php esc_html_e('Capuchina, borraja, viola, pensamiento, tagetes. Corte en floración plena. VPD controlado 0.8-1.2 kPa. Sin tratamientos post-cosecha.', 'castuo-agritech'); ?></p>
            <div class="product-specs">
              <span class="spec-tag">VPD 0.8–1.2</span>
              <span class="spec-tag">DLI &gt;14</span>
              <span class="spec-tag">Cosecha diaria</span>
              <span class="spec-tag">Sin postcosecha</span>
            </div>
            <div class="product-footer">
              <div class="product-moq">
                <strong><?php esc_html_e('Desde 100 u./var', 'castuo-agritech'); ?></strong><br>
                <span><?php esc_html_e('Pedido 48 h antelación', 'castuo-agritech'); ?></span>
              </div>
              <a href="<?php echo esc_url($cta_url); ?>" class="btn-product">
                <?php esc_html_e('Pedir muestra', 'castuo-agritech'); ?>
              </a>
            </div>
          </div>
        </article>

      </div>
    </div>
  </section>


  <!-- ═══ VALUE PROPS ═════════════════════════════════════════ -->
  <section class="section value-props-section" aria-labelledby="value-heading">
    <div class="container">

      <div class="section-header centered">
        <span class="section-label"><?php esc_html_e('¿Por qué CASTÚO?', 'castuo-agritech'); ?></span>
        <h2 id="value-heading"><?php esc_html_e('Valor real para tu negocio', 'castuo-agritech'); ?></h2>
      </div>

      <div class="value-grid">

        <div class="value-card">
          <div class="value-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          </div>
          <h4><?php esc_html_e('Trazabilidad immutable', 'castuo-agritech'); ?></h4>
          <p><?php esc_html_e('Hash SHA-256 en GaiaChain 3.0. Cada lote tiene su CID IPFS verificable por tu equipo de calidad.', 'castuo-agritech'); ?></p>
        </div>

        <div class="value-card">
          <div class="value-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>
          </div>
          <h4><?php esc_html_e('Energía solar certificada', 'castuo-agritech'); ?></h4>
          <p><?php esc_html_e('Más del 60% del cultivo con energía agrovoltaica propia. kWh generados registrados por lote.', 'castuo-agritech'); ?></p>
        </div>

        <div class="value-card">
          <div class="value-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 0 0 1.946-.806 3.42 3.42 0 0 1 4.438 0 3.42 3.42 0 0 0 1.946.806 3.42 3.42 0 0 1 3.138 3.138 3.42 3.42 0 0 0 .806 1.946 3.42 3.42 0 0 1 0 4.438 3.42 3.42 0 0 0-.806 1.946 3.42 3.42 0 0 1-3.138 3.138 3.42 3.42 0 0 0-1.946.806 3.42 3.42 0 0 1-4.438 0 3.42 3.42 0 0 0-1.946-.806 3.42 3.42 0 0 1-3.138-3.138 3.42 3.42 0 0 0-.806-1.946 3.42 3.42 0 0 1 0-4.438 3.42 3.42 0 0 0 .806-1.946 3.42 3.42 0 0 1 3.138-3.138z"/></svg>
          </div>
          <h4><?php esc_html_e('Certificación TRACES + REGEPA', 'castuo-agritech'); ?></h4>
          <p><?php esc_html_e('Certificados sanitarios UE automáticos. Documentación disponible antes del envío.', 'castuo-agritech'); ?></p>
        </div>

        <div class="value-card">
          <div class="value-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          </div>
          <h4><?php esc_html_e('Disponibilidad planificada', 'castuo-agritech'); ?></h4>
          <p><?php esc_html_e('Calendario semanal por cultivo. Sin sorpresas de stock. Notificación 72 h antes de cosecha.', 'castuo-agritech'); ?></p>
        </div>

        <div class="value-card">
          <div class="value-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
          </div>
          <h4><?php esc_html_e('100% infraestructura UE', 'castuo-agritech'); ?></h4>
          <p><?php esc_html_e('Datos y trazabilidad en servidores Hetzner + Arsys. Sin nube extracomunitaria. RGPD nativo.', 'castuo-agritech'); ?></p>
        </div>

        <div class="value-card">
          <div class="value-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
          </div>
          <h4><?php esc_html_e('Parámetros de cultivo en tiempo real', 'castuo-agritech'); ?></h4>
          <p><?php esc_html_e('pH, CE, O₂ disuelto, VPD y DLI monitorizados 24/7 vía LoRaWAN. Alertas automáticas.', 'castuo-agritech'); ?></p>
        </div>

      </div>
    </div>
  </section>


  <!-- ═══ TRACEABILITY ════════════════════════════════════════ -->
  <section class="section traceability-section" id="trazabilidad" aria-labelledby="trace-heading">
    <div class="container">
      <div class="traceability-inner">

        <div class="traceability-content">
          <span class="section-label"><?php esc_html_e('Blockchain · IPFS · QR', 'castuo-agritech'); ?></span>
          <h2 id="trace-heading"><?php esc_html_e('De la semilla al almacén, sin interrupciones en la cadena', 'castuo-agritech'); ?></h2>
          <p><?php esc_html_e('Cada evento del ciclo queda sellado en GaiaChain 3.0 (PoA, EU sovereign) con su CID en IPFS. El QR que entregamos a tu equipo de recepción verifica la integridad en tiempo real.', 'castuo-agritech'); ?></p>

          <div class="chain-steps" role="list" aria-label="<?php esc_attr_e('Etapas de trazabilidad', 'castuo-agritech'); ?>">
            <?php
            $steps = [
                [__('Siembra', 'castuo-agritech'),      __('Variedad + semilla + parcela SIGPAC registradas', 'castuo-agritech')],
                [__('Cultivo', 'castuo-agritech'),       __('pH, CE, O₂, VPD monitorizados cada 15 min vía IoT', 'castuo-agritech')],
                [__('Cosecha', 'castuo-agritech'),       __('Hash SHA-256 del lote pinned en IPFS', 'castuo-agritech')],
                [__('Certificación', 'castuo-agritech'), __('TRACES UE + certificado REGEPA emitidos', 'castuo-agritech')],
                [__('Entrega', 'castuo-agritech'),       __('QR inmutable entregado, verificable por el receptor', 'castuo-agritech')],
            ];
            foreach ($steps as $i => [$title, $desc]) : ?>
              <div class="chain-step" role="listitem">
                <div class="step-dot" aria-hidden="true"><?php echo $i + 1; ?></div>
                <div class="step-content">
                  <h4><?php echo esc_html($title); ?></h4>
                  <p><?php echo esc_html($desc); ?></p>
                </div>
              </div>
            <?php endforeach; ?>
          </div>
        </div>

        <!-- Demo card — datos de ejemplo (no datos reales) -->
        <div class="traceability-demo" role="region" aria-label="<?php esc_attr_e('Ejemplo de trazabilidad', 'castuo-agritech'); ?>">
          <div class="demo-header">
            <div class="demo-qr-placeholder" aria-hidden="true">⬛</div>
            <div class="demo-meta">
              <h4><?php esc_html_e('Lote INVH-ES28-MICGR-A4F2', 'castuo-agritech'); ?></h4>
              <p><?php esc_html_e('Microgreens girasol · 12 kg cosechados', 'castuo-agritech'); ?></p>
            </div>
          </div>

          <?php
          $demo_rows = [
              [__('pH medio cultivo', 'castuo-agritech'),    '5.94'],
              [__('CE (mS/cm)',       'castuo-agritech'),    '1.62'],
              [__('Energía solar',    'castuo-agritech'),    '67 %'],
              [__('IPFS CID',        'castuo-agritech'),    'QmX7aK…d3Fg'],
              [__('Blockchain TX',   'castuo-agritech'),    '0x8f2a…c9d1'],
              [__('TRACES cert.',    'castuo-agritech'),    'ES-2024-0847'],
              [__('Estado',         'castuo-agritech'),    '<span class="verified">✓ Verificado</span>'],
          ];
          ?>
          <div class="demo-data" aria-label="<?php esc_attr_e('Datos del lote de ejemplo', 'castuo-agritech'); ?>">
            <?php foreach ($demo_rows as [$label, $value]) : ?>
              <div class="demo-row">
                <span class="demo-label"><?php echo esc_html($label); ?></span>
                <span class="demo-value"><?php echo wp_kses_post($value); ?></span>
              </div>
            <?php endforeach; ?>
          </div>
        </div>

      </div>
    </div>
  </section>


  <!-- ═══ B2B CTA ══════════════════════════════════════════════ -->
  <section class="section b2b-section" id="contacto" aria-labelledby="b2b-heading">
    <div class="container">
      <div class="b2b-inner">
        <div class="b2b-content">
          <span class="section-label"><?php esc_html_e('Distribuidores · HoReCa · Retail', 'castuo-agritech'); ?></span>
          <h2 id="b2b-heading"><?php esc_html_e('¿Tu negocio necesita producto premium con trazabilidad verificable?', 'castuo-agritech'); ?></h2>
          <p><?php echo esc_html($moq_note); ?></p>
        </div>
        <div class="b2b-actions">
          <a href="mailto:<?php echo esc_attr($email); ?>?subject=<?php echo rawurlencode(__('Solicitud catálogo B2B — CASTÚO', 'castuo-agritech')); ?>"
             class="btn btn-primary">
            <?php esc_html_e('Contactar ahora', 'castuo-agritech'); ?>
          </a>
          <a href="<?php echo esc_url(home_url('/verificar/')); ?>" class="btn btn-outline" style="border-color:rgba(13,40,24,.25);color:var(--forest);">
            <?php esc_html_e('Verificar un lote', 'castuo-agritech'); ?>
          </a>
          <p class="b2b-note"><?php esc_html_e('Respuesta en menos de 24 h hábiles.', 'castuo-agritech'); ?></p>
        </div>
      </div>
    </div>
  </section>

</main>

<?php get_footer(); ?>
