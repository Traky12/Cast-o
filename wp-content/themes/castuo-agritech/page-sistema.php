<?php
/**
 * Template Name: Sistema CASTUO
 * Resumen tecnico-operativo y de cumplimiento para clientes/partners.
 */
get_header();

$tam_value = get_theme_mod('castuo_tam_value', 'EUR 16.96B');
$sam_value = get_theme_mod('castuo_sam_value', 'EUR 2.40B');
$som_value = get_theme_mod('castuo_som_value', 'EUR 120M');
$farms_target = get_theme_mod('castuo_farms_target', '1.012 farms');

$rgpd_summary = get_theme_mod('castuo_rgpd_summary', '100% compliant con RGPD Art. 30 y gobernanza de datos trazable.');
$iso_summary = get_theme_mod('castuo_iso_summary', 'Controles ISO 27001 con auditoria operativa y revisiones periodicas de acceso.');
$ai_act_summary = get_theme_mod('castuo_ai_act_summary', 'Human-in-the-loop en decisiones criticas y trazabilidad completa de inferencias.');
$nis2_cra_summary = get_theme_mod('castuo_nis2_cra_summary', 'NIS2 + CRA con runbooks de incidentes, observabilidad y politicas CI/CD seguras.');

$roadmap_hits = new WP_Query([
  'post_type'      => 'roadmap_hit',
  'post_status'    => 'publish',
  'posts_per_page' => 6,
  'orderby'        => 'date',
  'order'          => 'ASC',
]);
?>

<main id="main" role="main">
  <section class="section system-hero" aria-labelledby="system-heading">
    <div class="container">
      <div class="system-hero-inner">
        <span class="section-label">CASTUO-SYSTEM v2.1</span>
        <h1 id="system-heading">Plataforma soberana para invernaderos autonomos</h1>
        <p>
          Operacion integral de cultivo con IA supervisada, trazabilidad verificable y cumplimiento normativo europeo.
          Arquitectura preparada para escalado multi-tenant y auditoria continua.
        </p>
        <div class="system-hero-actions">
          <a href="<?php echo esc_url(castuo_page_url('verificar')); ?>" class="btn btn-primary"><?php esc_html_e('Verificar lote', 'castuo-agritech'); ?></a>
          <a href="<?php echo esc_url(home_url('/#contacto')); ?>" class="btn btn-outline"><?php esc_html_e('Contactar equipo B2B', 'castuo-agritech'); ?></a>
        </div>
      </div>
    </div>
  </section>

  <section class="section system-metrics" aria-labelledby="metrics-heading">
    <div class="container">
      <div class="section-header centered">
        <span class="section-label">Mercado y crecimiento</span>
        <h2 id="metrics-heading">Metricas editables desde WordPress</h2>
      </div>
      <div class="metrics-grid" role="list">
        <article class="metric-card" role="listitem">
          <span class="metric-label">TAM</span>
          <strong class="metric-value"><?php echo esc_html($tam_value); ?></strong>
        </article>
        <article class="metric-card" role="listitem">
          <span class="metric-label">SAM</span>
          <strong class="metric-value"><?php echo esc_html($sam_value); ?></strong>
        </article>
        <article class="metric-card" role="listitem">
          <span class="metric-label">SOM / ARR</span>
          <strong class="metric-value"><?php echo esc_html($som_value); ?></strong>
        </article>
        <article class="metric-card" role="listitem">
          <span class="metric-label">Escala objetivo</span>
          <strong class="metric-value"><?php echo esc_html($farms_target); ?></strong>
        </article>
      </div>
    </div>
  </section>

  <section class="section system-grid-section" aria-labelledby="stack-heading">
    <div class="container">
      <div class="section-header">
        <span class="section-label">Stack operativo</span>
        <h2 id="stack-heading">Capas tecnicas del sistema</h2>
      </div>

      <div class="system-grid">
        <article class="system-card">
          <h3>IoT y Telemetria</h3>
          <p>Ingesta de sensores por shard con pipeline MQTT/API y almacenamiento de series temporales.</p>
          <ul>
            <li>Frecuencia de captura configurable por perfil</li>
            <li>Normalizacion y validacion de payloads</li>
            <li>Persistencia en PostgreSQL/TimescaleDB</li>
          </ul>
        </article>

        <article class="system-card">
          <h3>Sabionda IA</h3>
          <p>Motor de decision agronomica con reglas de seguridad y trazabilidad para acciones criticas.</p>
          <ul>
            <li>Evaluacion de anomalias y riesgo</li>
            <li>Fallback de proveedores de inferencia</li>
            <li>Human-in-the-loop en umbrales sensibles</li>
          </ul>
        </article>

        <article class="system-card">
          <h3>Actuacion y Control</h3>
          <p>Comandos operativos a riego, ventilacion, iluminacion y nutricion con acuse de recibo.</p>
          <ul>
            <li>Politicas por cultivo y fenologia</li>
            <li>Bitacora de cambios por lote</li>
            <li>Rollback de configuraciones</li>
          </ul>
        </article>

        <article class="system-card">
          <h3>Seguridad y Cumplimiento</h3>
          <p>Controles de identidad, autorizacion y evidencia para auditorias internas y externas.</p>
          <ul>
            <li>JWT dispositivos + RBAC</li>
            <li>Firma eIDAS2 de documentos/payloads</li>
            <li>Monitoreo de riesgos RGPD/NIS2</li>
          </ul>
        </article>
      </div>
    </div>
  </section>

  <section class="section compliance-section" aria-labelledby="compliance-heading">
    <div class="container">
      <div class="section-header centered">
        <span class="section-label">Compliance UE</span>
        <h2 id="compliance-heading">Marco normativo implementado</h2>
      </div>

      <div class="compliance-table" role="table" aria-label="Cobertura normativa">
        <div class="compliance-row compliance-head" role="row">
          <span role="columnheader">Normativa</span>
          <span role="columnheader">Control aplicado</span>
          <span role="columnheader">Evidencia tecnica</span>
        </div>
        <div class="compliance-row" role="row">
          <span role="cell">RGPD</span>
          <span role="cell">Minimizacion y gobernanza de datos</span>
          <span role="cell"><?php echo esc_html($rgpd_summary); ?></span>
        </div>
        <div class="compliance-row" role="row">
          <span role="cell">ISO 27001</span>
          <span role="cell">Controles operativos y revision de accesos</span>
          <span role="cell"><?php echo esc_html($iso_summary); ?></span>
        </div>
        <div class="compliance-row" role="row">
          <span role="cell">AI Act</span>
          <span role="cell">Supervision humana en decisiones criticas</span>
          <span role="cell"><?php echo esc_html($ai_act_summary); ?></span>
        </div>
        <div class="compliance-row" role="row">
          <span role="cell">NIS2 / CRA</span>
          <span role="cell">Resiliencia operativa y seguridad por diseno</span>
          <span role="cell"><?php echo esc_html($nis2_cra_summary); ?></span>
        </div>
      </div>
    </div>
  </section>

  <section class="section roadmap-section" aria-labelledby="roadmap-heading">
    <div class="container">
      <div class="section-header">
        <span class="section-label">Roadmap</span>
        <h2 id="roadmap-heading">Proximos entregables de producto</h2>
      </div>
      <div class="roadmap-list" role="list">
        <?php if ($roadmap_hits->have_posts()) : ?>
          <?php while ($roadmap_hits->have_posts()) : $roadmap_hits->the_post(); ?>
            <?php
            $quarter = get_post_meta(get_the_ID(), 'quarter', true);
            $status = get_post_meta(get_the_ID(), 'status', true);
            $status_label = [
                'planned' => 'Planificado',
                'in_progress' => 'En progreso',
                'done' => 'Completado',
            ][$status] ?? 'Planificado';
            ?>
            <article class="roadmap-item" role="listitem">
              <h3><?php the_title(); ?></h3>
              <p><?php echo esc_html(get_the_excerpt() ?: wp_strip_all_tags(get_the_content())); ?></p>
              <div class="roadmap-meta">
                <?php if (! empty($quarter)) : ?><span><?php echo esc_html($quarter); ?></span><?php endif; ?>
                <span class="roadmap-status roadmap-status-<?php echo esc_attr($status ?: 'planned'); ?>"><?php echo esc_html($status_label); ?></span>
              </div>
            </article>
          <?php endwhile; ?>
          <?php wp_reset_postdata(); ?>
        <?php else : ?>
          <article class="roadmap-item" role="listitem">
            <h3><?php esc_html_e('Roadmap en preparacion', 'castuo-agritech'); ?></h3>
            <p><?php esc_html_e('Crea hitos en el panel de WordPress para mostrar la planificacion dinamica.', 'castuo-agritech'); ?></p>
          </article>
        <?php endif; ?>
      </div>
      <p class="roadmap-cta-wrap">
        <a class="btn btn-outline" href="<?php echo esc_url(castuo_page_url('roadmap')); ?>"><?php esc_html_e('Ver roadmap completo', 'castuo-agritech'); ?></a>
      </p>
    </div>
  </section>
</main>

<?php get_footer(); ?>
