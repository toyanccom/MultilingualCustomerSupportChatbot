<?php
/**
 * Plugin Name: Multilingual CS Chatbot Widget
 * Description: Drop-in widget that connects WordPress sites to the Multilingual Customer Support Chatbot HTTP API.
 * Version: 0.1.0
 * Author: Multilingual Customer Support Chatbot Team
 * License: MIT
 */

if (!defined('ABSPATH')) {
    exit;
}

const MCS_CHATBOT_ENDPOINT_OPTION = 'mcs_chatbot_endpoint';
const MCS_CHATBOT_API_KEY_OPTION = 'mcs_chatbot_api_key';

function mcs_chatbot_register_settings()
{
    register_setting(
        'mcs_chatbot_options',
        MCS_CHATBOT_ENDPOINT_OPTION,
        [
            'type' => 'string',
            'sanitize_callback' => 'esc_url_raw',
            'default' => 'https://your-api.example.com',
        ]
    );

    register_setting(
        'mcs_chatbot_options',
        MCS_CHATBOT_API_KEY_OPTION,
        [
            'type' => 'string',
            'sanitize_callback' => 'sanitize_text_field',
            'default' => '',
        ]
    );
}
add_action('admin_init', 'mcs_chatbot_register_settings');

function mcs_chatbot_settings_page()
{
    if (!current_user_can('manage_options')) {
        return;
    }

    ?>
    <div class="wrap">
        <h1><?php esc_html_e('Multilingual CS Chatbot', 'mcs-chatbot'); ?></h1>
        <form method="post" action="options.php">
            <?php
            settings_fields('mcs_chatbot_options');
            do_settings_sections('mcs_chatbot_options');
            $endpoint = esc_url(get_option(MCS_CHATBOT_ENDPOINT_OPTION, 'https://your-api.example.com'));
            $api_key = esc_attr(get_option(MCS_CHATBOT_API_KEY_OPTION, ''));
            ?>
            <table class="form-table" role="presentation">
                <tr>
                    <th scope="row">
                        <label for="mcs_chatbot_endpoint"><?php esc_html_e('Chat API URL', 'mcs-chatbot'); ?></label>
                    </th>
                    <td>
                        <input
                            name="<?php echo esc_attr(MCS_CHATBOT_ENDPOINT_OPTION); ?>"
                            type="url"
                            id="mcs_chatbot_endpoint"
                            value="<?php echo $endpoint; ?>"
                            class="regular-text"
                            placeholder="https://your-api.example.com"
                            required
                        />
                        <p class="description">
                            <?php esc_html_e('Point this to the chatbot server you host (e.g. https://example.com). The widget automatically calls /chat and /sessions/{id}.', 'mcs-chatbot'); ?>
                        </p>
                    </td>
                </tr>
                <tr>
                    <th scope="row">
                        <label for="mcs_chatbot_api_key"><?php esc_html_e('API key header', 'mcs-chatbot'); ?></label>
                    </th>
                    <td>
                        <input
                            name="<?php echo esc_attr(MCS_CHATBOT_API_KEY_OPTION); ?>"
                            type="text"
                            id="mcs_chatbot_api_key"
                            value="<?php echo $api_key; ?>"
                            class="regular-text"
                            placeholder="<?php esc_attr_e('Optional shared secret', 'mcs-chatbot'); ?>"
                        />
                        <p class="description">
                            <?php esc_html_e('If your chatbot server requires the X-API-Key header, paste it here. Leaving this empty keeps the request unauthenticated.', 'mcs-chatbot'); ?>
                        </p>
                    </td>
                </tr>
            </table>
            <?php submit_button(); ?>
        </form>
    </div>
    <?php
}

function mcs_chatbot_register_admin_menu()
{
    add_options_page(
        __('Multilingual CS Chatbot', 'mcs-chatbot'),
        __('Multilingual CS Chatbot', 'mcs-chatbot'),
        'manage_options',
        'mcs-chatbot',
        'mcs_chatbot_settings_page'
    );
}
add_action('admin_menu', 'mcs_chatbot_register_admin_menu');

function mcs_chatbot_register_assets()
{
    $plugin_url = plugin_dir_url(__FILE__);
    wp_register_style(
        'mcs-chatbot-widget',
        $plugin_url . 'assets/widget.css',
        [],
        '0.1.0'
    );
    wp_register_script(
        'mcs-chatbot-widget',
        $plugin_url . 'assets/widget.js',
        [],
        '0.1.0',
        true
    );

    $endpoint = get_option(MCS_CHATBOT_ENDPOINT_OPTION, 'https://your-api.example.com');
    $endpoint = untrailingslashit($endpoint);
    $api_key = get_option(MCS_CHATBOT_API_KEY_OPTION, '');

    wp_localize_script(
        'mcs-chatbot-widget',
        'MCSChatbot',
        [
            'chatEndpoint' => $endpoint . '/chat',
            'sessionEndpoint' => $endpoint . '/sessions/',
            'apiKey' => $api_key,
            'strings' => [
                'widgetTitle' => __('Support Assistant', 'mcs-chatbot'),
                'inputLabel' => __('Ask a question', 'mcs-chatbot'),
                'placeholder' => __('Type your message…', 'mcs-chatbot'),
                'sendButton' => __('Send', 'mcs-chatbot'),
                'resetButton' => __('Clear chat', 'mcs-chatbot'),
                'errorMessage' => __('Sorry, something went wrong. Please try again.', 'mcs-chatbot'),
            ],
        ]
    );
}
add_action('init', 'mcs_chatbot_register_assets');

function mcs_chatbot_render_shortcode($atts, $content = '', $tag = '')
{
    wp_enqueue_style('mcs-chatbot-widget');
    wp_enqueue_script('mcs-chatbot-widget');

    ob_start();
    ?>
    <div
        class="mcs-chatbot-widget"
        role="region"
        aria-live="polite"
        data-chat-endpoint="<?php echo esc_attr($endpoint . '/chat'); ?>"
        data-session-endpoint="<?php echo esc_attr($endpoint . '/sessions/'); ?>"
    >
        <div class="mcs-chatbot-header">
            <strong class="mcs-chatbot-title"><?php esc_html_e('Support Assistant', 'mcs-chatbot'); ?></strong>
        </div>
        <div class="mcs-chatbot-history"></div>
        <form class="mcs-chatbot-form" novalidate>
            <label class="mcs-chatbot-label">
                <span class="screen-reader-text"><?php esc_html_e('Ask a question', 'mcs-chatbot'); ?></span>
                <textarea
                    class="mcs-chatbot-input"
                    rows="3"
                    required
                    placeholder="<?php echo esc_attr__('Type your message…', 'mcs-chatbot'); ?>"
                ></textarea>
            </label>
            <div class="mcs-chatbot-actions">
                <button type="submit" class="mcs-chatbot-send button button-primary">
                    <?php esc_html_e('Send', 'mcs-chatbot'); ?>
                </button>
                <button type="button" class="mcs-chatbot-reset button">
                    <?php esc_html_e('Clear chat', 'mcs-chatbot'); ?>
                </button>
            </div>
        </form>
    </div>
    <?php
    return ob_get_clean();
}
add_shortcode('mcs_chatbot', 'mcs_chatbot_render_shortcode');
