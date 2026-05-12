<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
  <meta charset="<?php bloginfo('charset'); ?>">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="<?php echo esc_attr(get_bloginfo('description')); ?>">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<a class="skip-link sr-only" href="#main"><?php esc_html_e('Saltar al contenido', 'castuo-agritech'); ?></a>

<header class="site-header" id="site-header" role="banner">
  <div class="container">
    <div class="header-inner">

      <!-- Logo / Brand -->
      <a href="<?php echo esc_url(home_url('/')); ?>" class="site-logo" rel="home">
        <?php if (has_custom_logo()) : ?>
          <?php the_custom_logo(); ?>
        <?php else : ?>
          <span class="logo-mark" aria-hidden="true">
            <svg viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
              <!-- Leaf / sprout mark -->
              <path d="M9 15V7M9 7C9 7 5 7 5 3C5 3 9 3 9 7ZM9 7C9 7 13 7 13 3C13 3 9 3 9 7Z"/>
            </svg>
          </span>
          <span><?php bloginfo('name'); ?></span>
        <?php endif; ?>
      </a>

      <!-- Primary Navigation -->
      <button class="menu-toggle" aria-expanded="false" aria-controls="primary-menu" aria-label="<?php esc_attr_e('Menú', 'castuo-agritech'); ?>">
        <span></span><span></span><span></span>
      </button>

      <nav class="site-nav" id="primary-menu" role="navigation" aria-label="<?php esc_attr_e('Navegación principal', 'castuo-agritech'); ?>">
        <?php
        wp_nav_menu([
            'theme_location' => 'primary',
            'container'      => false,
            'items_wrap'     => '%3$s',
            'depth'          => 1,
            'fallback_cb'    => function () {
                echo '<a href="' . esc_url(home_url('/')) . '">' . esc_html__('Inicio', 'castuo-agritech') . '</a>';
              echo '<a href="' . esc_url(castuo_page_url('sistema')) . '">' . esc_html__('Sistema', 'castuo-agritech') . '</a>';
              echo '<a href="' . esc_url(castuo_page_url('roadmap')) . '">' . esc_html__('Roadmap', 'castuo-agritech') . '</a>';
                echo '<a href="#productos">'    . esc_html__('Productos', 'castuo-agritech')    . '</a>';
                echo '<a href="#trazabilidad">' . esc_html__('Trazabilidad', 'castuo-agritech') . '</a>';
                echo '<a href="#contacto">'     . esc_html__('Contacto B2B', 'castuo-agritech') . '</a>';
              echo '<a href="' . esc_url(castuo_page_url('verificar')) . '" class="header-cta">' . esc_html__('Verificar QR', 'castuo-agritech') . '</a>';
            },
        ]);
        ?>
      </nav>

    </div>
  </div>
</header>
