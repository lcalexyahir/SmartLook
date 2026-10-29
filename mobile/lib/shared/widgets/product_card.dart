// mobile/lib/shared/widgets/product_card.dart
//
// MODIFICADO (SaaS - A.1): muestra "Vendido por <empresa>" en el catálogo
// unificado.
import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../../core/models/product_model.dart';
import '../theme/app_colors.dart';

class ProductCard extends StatelessWidget {
  final Product product;
  final VoidCallback? onTap;

  const ProductCard({
    super.key,
    required this.product,
    this.onTap,
  });

  String getPriceRange() {
    if (product.variantes.isEmpty) return 'Sin precio';
    final prices = product.variantes.map((v) => v.precio).toList();
    final min = prices.reduce((a, b) => a < b ? a : b);
    final max = prices.reduce((a, b) => a > b ? a : b);
    if (min == max) return 'Bs ${min.toStringAsFixed(2)}';
    return 'Bs ${min.toStringAsFixed(2)} - Bs ${max.toStringAsFixed(2)}';
  }

  @override
  Widget build(BuildContext context) {
    final empresa = product.empresaNombre ?? '';
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Card(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // La imagen ocupa el espacio que sobra después del texto,
            // así nunca desborda sin importar el childAspectRatio del grid.
            Expanded(
              child: ClipRRect(
                borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
                child: product.imagenProducto != null
                    ? CachedNetworkImage(
                        imageUrl: product.imagenProducto!,
                        width: double.infinity,
                        fit: BoxFit.cover,
                        placeholder: (context, url) => Container(
                          color: AppColors.greyLight,
                          child: const Center(
                            child: CircularProgressIndicator(),
                          ),
                        ),
                        errorWidget: (context, url, error) => Container(
                          color: AppColors.greyLight,
                          child: const Icon(
                            Icons.image_not_supported,
                            size: 48,
                            color: AppColors.grey,
                          ),
                        ),
                      )
                    : Container(
                        color: AppColors.greyLight,
                        child: const Icon(
                          Icons.shopping_bag,
                          size: 48,
                          color: AppColors.grey,
                        ),
                      ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    product.marca?.nombre ?? 'SmartLook',
                    style: const TextStyle(
                      fontSize: 11,
                      color: AppColors.grey,
                      letterSpacing: 1,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    product.nombre,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: AppColors.dark,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    product.categoria?.nombre ?? '',
                    style: const TextStyle(
                      fontSize: 13,
                      color: AppColors.grey,
                    ),
                  ),
                  // NUEVO (SaaS - A.1): tienda que vende la prenda.
                  if (empresa.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        const Icon(Icons.storefront, size: 13, color: AppColors.grey),
                        const SizedBox(width: 4),
                        Expanded(
                          child: Text(
                            'Vendido por $empresa',
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              fontSize: 12,
                              color: AppColors.dark,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                  const SizedBox(height: 8),
                  Text(
                    getPriceRange(),
                    style: const TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w700,
                      color: AppColors.accent,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}