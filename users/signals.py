# from django.db.models.signals import pre_save
# from django.dispatch import receiver
# from django.contrib.auth.models import User
#
# @receiver(pre_save, sender=User)
# def hash_user_password(sender, instance, **kwargs):
#     if instance.pk:  # Vérifie que l'utilisateur existe déjà
#         original_user = User.objects.get(pk=instance.pk)
#         if original_user.password != instance.password:  # Si le mot de passe a changé
#             instance.set_password(instance.password)
