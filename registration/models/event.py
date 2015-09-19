from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _


from .badge import BadgeSettings


class Event(models.Model):
    """ Event for registration.

    Columns:
        :url_name: the ID of the event used in URLs
        :name: the name of the event
        :text: text at begin of registration
        :imprint: text at the bottom if the registration page
        :registered: text after the successful registration
        :email: e-mail address used as sender of automatic e-mails
        :active: is the registration opened?
        :admins: list of admins of this event, they can see and edit everything
        :ask_shirt: ask for the t-shirt size during registration
        :ask_vegetarian: ask, if the helper is vegetarian
        :show_public_numbers: show the number of current and maximal helpers on
                             the registration page
        :mail_validation: helper must validate his mail address by a link
        :badge: use the badge creation system
    """

    url_name = models.CharField(
        max_length=200,
        unique=True,
        validators=[RegexValidator('^[a-zA-Z0-9]+$')],
        verbose_name=_("Name for URL"),
        help_text=_("May contain the following chars: a-zA-Z0-9."),
    )

    name = models.CharField(
        max_length=200,
        verbose_name=_("Event name"),
    )

    text = models.TextField(
        blank=True,
        verbose_name=_("Text before registration"),
        help_text=_("Displayed as first text of the registration form."),
    )

    imprint = models.TextField(
        blank=True,
        verbose_name=_('Imprint'),
        help_text=_("Display at the bottom of the registration form."),
    )

    registered = models.TextField(
        blank=True,
        verbose_name=_("Text after registration"),
        help_text=_("Displayed after registration."),
    )

    email = models.EmailField(
        default='party@fs.tum.de',
        verbose_name=_("E-Mail"),
        help_text=_("Used as sender of e-mails."),
    )

    active = models.BooleanField(
        default=False,
        verbose_name=_("Registration possible"),
    )

    admins = models.ManyToManyField(
        User,
        blank=True,
    )

    ask_shirt = models.BooleanField(
        default=True,
        verbose_name=_("Ask for T-shirt size"),
    )

    ask_vegetarian = models.BooleanField(
        default=True,
        verbose_name=_("Ask, if helper is vegetarian"),
    )

    show_public_numbers = models.BooleanField(
        default=True,
        verbose_name=_("Show number of helpers on registration page"),
    )

    mail_validation = models.BooleanField(
        default=True,
        verbose_name=_("Registrations for public shifts must be validated by "
                       "a link that is sent per mail"),
    )

    badges = models.BooleanField(
        default=False,
        verbose_name=_("Use badge creation"),
    )

    def __str__(self):
        return self.name

    def is_admin(self, user):
        """ Check, if a user is admin of this event and returns a boolean.

        A superuser is also admin of an event.

        :param user: the user
        :type user: :class:`django.contrib.auth.models.User`

        :returns: True or False
        """
        return user.is_superuser or self.admins.filter(pk=user.pk).exists()

    def is_involved(self, user):
        """ Check if is_admin is fulfilled or the user is admin of a job.

        :param user: the user
        :type user: :class:`django.contrib.auth.models.User`
        """
        if self.is_admin(user):
            return True

        # iterate over all jobs
        for job in self.job_set.all():
            if job.job_admins.filter(pk=user.pk).exists():
                return True

        return False

    @property
    def public_jobs(self):
        return self.job_set.filter(public=True)

    @property
    def badge_settings(self):
        try:
            return self.badgesettings
        except AttributeError:
            return None


@receiver(post_save, sender=Event, dispatch_uid='event_saved')
def event_saved(sender, instance, using, **kwargs):
    """ Add badge settings if necessary.

    This is a signal handler, that is called, when a event is saved. It
    adds the badge settings if badge creation is enabled and it is not
    there already.
    """
    if instance.badges and not instance.badge_settings:
        settings = BadgeSettings()
        settings.event = instance
        settings.save()
