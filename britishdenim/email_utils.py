from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.urls import reverse


def _send_post_status_email(request, post, subject, template_name, include_feed_link=False):
    if not post.user_id.email:
        return False

    try:
        feed_url = request.build_absolute_uri(
            reverse('sku_feed', kwargs={'sku': post.sku.sku}),
        )
        first_name = post.user_id.first_name or post.user_id.username
        message = (
            f'Hola {first_name},\n\n'
            f'{subject}.\n\n'
            f'{"Puedes ver la publicación aquí: " + feed_url if include_feed_link else ""}\n\n'
            'British Denim'
        )
        html_message = render_to_string(
            template_name,
            {
                'first_name': first_name,
                'sku': post.sku.sku,
                'product_name': post.sku.name,
                'feed_url': feed_url,
                'logo_url': request.build_absolute_uri(static('britishdenim/images/logo.png')),
            },
        )
        email = EmailMultiAlternatives(subject, message, settings.DEFAULT_FROM_EMAIL, [post.user_id.email])
        email.attach_alternative(html_message, 'text/html')
        email.send()
    except Exception:
        return False
    return True


def send_post_review_email(request, post):
    return _send_post_status_email(
        request,
        post,
        'Tu publicación está siendo revisada',
        'britishdenim/emails/post_under_review.html',
    )


def send_post_approval_email(request, post):
    return _send_post_status_email(
        request,
        post,
        'Tu publicación fue aprobada',
        'britishdenim/emails/post_approved.html',
        include_feed_link=True,
    )
