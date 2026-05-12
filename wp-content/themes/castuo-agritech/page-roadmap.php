<?php
/**
 * Template Name: Roadmap CASTUO
 * Vista completa de hitos del roadmap gestionados por CPT.
 */
get_header();

$roadmap_hits = new WP_Query([
    'post_type'      => 'roadmap_hit',
    'post_status'    => 'publish',
    'posts_per_page' => -1,
    'orderby'        => 'date',
    'order'          => 'ASC',
]);
?>

<main id="main" role="main">
  <section class="section roadmap-page-hero" aria-labelledby="roadmap-page-heading">
    <div class="container">
      <span class="section-label">Roadmap CASTUO-SYSTEM</span>
      <h1 id="roadmap-page-heading">Plan de entregables 2026-2027</h1>
      <p>Hitos de producto, cumplimiento y operaciones gestionados como contenido editable desde WordPress.</p>
    </div>
  </section>

  <section class="section roadmap-page-content" aria-labelledby="roadmap-list-heading">
    <div class="container">
      <div class="section-header">
        <h2 id="roadmap-list-heading">Hitos publicados</h2>
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
            <h3><?php esc_html_e('Sin hitos todavia', 'castuo-agritech'); ?></h3>
            <p><?php esc_html_e('Crea entradas de tipo "Hitos Roadmap" desde wp-admin para poblar esta pagina.', 'castuo-agritech'); ?></p>
          </article>
        <?php endif; ?>
      </div>
    </div>
  </section>
</main>

<?php get_footer(); ?>
