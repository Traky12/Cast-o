<?php
/**
 * Fallback template — blog/archive.
 * Not used for front page (handled by front-page.php).
 */
get_header();
?>
<main id="main" class="section" role="main">
  <div class="container">
    <?php if (have_posts()) : while (have_posts()) : the_post(); ?>
      <article <?php post_class(); ?>>
        <h2><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
        <div><?php the_excerpt(); ?></div>
      </article>
    <?php endwhile; else : ?>
      <p><?php esc_html_e('No se encontró contenido.', 'castuo-agritech'); ?></p>
    <?php endif; ?>
  </div>
</main>
<?php get_footer(); ?>
