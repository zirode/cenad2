[app]
# Informations de l'application
title = CENAD
package.name = cenad
package.domain = mg.una.cenad
version = 1.0.0

# Fichier principal
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db,sql,csv
source.include_patterns = assets/*,data/*,ui/*,utils/*

# Icône APK (placée dans assets/logos/)
icon.filename = %(source.dir)s/assets/logos/cenad_logo.png

# Orientation (portrait uniquement pour mobile)
orientation = portrait

# Permissions Android
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# SDK Android
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True

# Architecture (ARM pour la plupart des téléphones)
android.archs = arm64-v8a, armeabi-v7a

# Dépendances Python
requirements = python3,kivy==2.3.0,kivymd,plyer,setuptools


# Kivy bootstrap
p4a.bootstrap = sdl2

[buildozer]
# Dossier de build
build.dir = ./.buildozer

# Niveau de log (0=error, 1=info, 2=debug)
log_level = 1

# Avertissement si buildozer n'est pas dans le PATH
warn_on_root = 1

