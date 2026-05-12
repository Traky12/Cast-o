<footer class="site-footer" role="contentinfo">
  <div class="container">
    <div class="footer-inner">

      <div class="footer-logo">CASTÚO™</div>

      <nav class="footer-links" aria-label="<?php esc_attr_e('Navegación pie de página', 'castuo-agritech'); ?>">
        <?php
        wp_nav_menu([
            'theme_location' => 'footer',
            'container'      => false,
            'items_wrap'     => '%3$s',
            'depth'          => 1,
            'fallback_cb'    => function () {
                echo '<a href="' . esc_url(castuo_page_url('verificar')) . '">' . esc_html__('Verificar QR', 'castuo-agritech') . '</a>';
              echo '<a href="' . esc_url(castuo_page_url('roadmap')) . '">' . esc_html__('Roadmap', 'castuo-agritech') . '</a>';
                echo '<a href="' . esc_url(get_privacy_policy_url()) . '">' . esc_html__('Privacidad', 'castuo-agritech') . '</a>';
                echo '<a href="mailto:' . esc_attr(get_theme_mod('castuo_contact_email', 'b2b@castuo360.eu')) . '">' . esc_html__('Contacto', 'castuo-agritech') . '</a>';
            },
        ]);
        ?>
      </nav>

      <p class="footer-legal">
        &copy; <?php echo esc_html(date('Y')); ?> CASTÚO-SYSTEM™ &mdash;
        <?php esc_html_e('Infraestructura 100% UE · RGPD · AI Act · eIDAS', 'castuo-agritech'); ?>
      </p>

    </div>
  </div>
</footer>

<?php wp_footer(); ?>
</body>
</html>
