# Stripe: la app no usa "push provisioning" (agregar tarjetas a Google Pay),
# pero el plugin referencia esas clases y R8 falla si no las encuentra.
-dontwarn com.stripe.android.pushProvisioning.**