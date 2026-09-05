import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:provider/provider.dart';
import '../../../../core/models/product_model.dart' as model;
import '../../../core/network/api_client.dart';
import '../../../shared/theme/app_colors.dart';
import '../../../shared/widgets/loading_overlay.dart';
import '../data/repositories/catalog_repository_impl.dart';
import '../data/sources/catalog_remote_source.dart';

class ProductDetailScreen extends StatefulWidget {
  final int productId;

  const ProductDetailScreen({super.key, required this.productId});

  @override
  State<ProductDetailScreen> createState() => _ProductDetailScreenState();
}

class _ProductDetailScreenState extends State<ProductDetailScreen> {
  late final CatalogRepositoryImpl _catalogRepository;
  model.Product? _product;
  model.ProductVariant? _selectedVariant;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    final apiClient = context.read<ApiClient>();
    _catalogRepository = CatalogRepositoryImpl(
      remoteSource: CatalogRemoteSource(apiClient: apiClient),
    );
    _loadProduct();
  }

  Future<void> _loadProduct() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final entity = await _catalogRepository.getProduct(widget.productId);
      final product = entity.toModel();

      // Recargar con datos completos
      final apiClient = context.read<ApiClient>();
      final response = await apiClient.dio.get('/catalog/productos/${widget.productId}/');
      final fullProduct = model.Product.fromJson(response.data);

      if (mounted) {
        setState(() {
          _product = fullProduct;
          if (fullProduct.variantes.isNotEmpty) {
            _selectedVariant = fullProduct.variantes.first;
          }
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_product?.nombre ?? 'Detalle de Producto'),
      ),
      body: LoadingOverlay(
        isLoading: _isLoading,
        child: _product == null
            ? const Center(child: Text('Producto no encontrado'))
            : SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Imagen
                    Container(
                      height: 350,
                      width: double.infinity,
                      color: AppColors.greyLight,
                      child: _product!.imagenProducto != null
                          ? CachedNetworkImage(
                              imageUrl: _product!.imagenProducto!,
                              fit: BoxFit.cover,
                              placeholder: (context, url) => const Center(
                                child: CircularProgressIndicator(),
                              ),
                              errorWidget: (context, url, error) => const Icon(
                                Icons.shopping_bag,
                                size: 64,
                                color: AppColors.grey,
                              ),
                            )
                          : const Icon(
                              Icons.shopping_bag,
                              size: 64,
                              color: AppColors.grey,
                            ),
                    ),
                    Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _product!.marca?.nombre ?? 'SmartLook',
                            style: const TextStyle(
                              fontSize: 12,
                              color: AppColors.grey,
                              letterSpacing: 1.5,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            _product!.nombre,
                            style: const TextStyle(
                              fontSize: 24,
                              fontWeight: FontWeight.bold,
                              color: AppColors.dark,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            _product!.categoria?.nombre ?? '',
                            style: const TextStyle(
                              fontSize: 14,
                              color: AppColors.grey,
                            ),
                          ),
                          const SizedBox(height: 16),
                          if (_product!.descripcion != null)
                            Text(
                              _product!.descripcion!,
                              style: const TextStyle(
                                fontSize: 14,
                                height: 1.5,
                              ),
                            ),
                          const SizedBox(height: 16),
                          Row(
                            children: [
                              _buildInfoChip(
                                Icons.checkroom,
                                _product!.tipoPrenda,
                              ),
                              const SizedBox(width: 8),
                              _buildInfoChip(
                                Icons.person,
                                _product!.genero,
                              ),
                            ],
                          ),
                          const SizedBox(height: 24),
                          // Variantes
                          if (_product!.variantes.isNotEmpty) ...[
                            const Text(
                              'Variantes Disponibles',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            const SizedBox(height: 12),
                            Wrap(
                              spacing: 8,
                              runSpacing: 8,
                              children: _product!.variantes.map((variant) {
                                final isSelected = _selectedVariant?.idVariante ==
                                    variant.idVariante;
                                return InkWell(
                                  onTap: () {
                                    setState(() {
                                      _selectedVariant = variant;
                                    });
                                  },
                                  child: Container(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 12,
                                      vertical: 8,
                                    ),
                                    decoration: BoxDecoration(
                                      color: isSelected
                                          ? AppColors.accent
                                          : AppColors.white,
                                      border: Border.all(
                                        color: isSelected
                                            ? AppColors.accent
                                            : AppColors.greyLight,
                                      ),
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        Container(
                                          width: 16,
                                          height: 16,
                                          decoration: BoxDecoration(
                                            color: Color(
                                              variant.color?.colorValue ??
                                                  0xFF808080,
                                            ),
                                            shape: BoxShape.circle,
                                            border: Border.all(
                                              color: AppColors.grey,
                                            ),
                                          ),
                                        ),
                                        const SizedBox(width: 8),
                                        Text(
                                          '${variant.talla?.nombre} - ${variant.color?.nombre}',
                                          style: TextStyle(
                                            color: isSelected
                                                ? AppColors.white
                                                : AppColors.dark,
                                          ),
                                        ),
                                        const SizedBox(width: 8),
                                        Text(
                                          'Bs ${variant.precio.toStringAsFixed(2)}',
                                          style: TextStyle(
                                            fontWeight: FontWeight.w600,
                                            color: isSelected
                                                ? AppColors.white
                                                : AppColors.accent,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                );
                              }).toList(),
                            ),
                          ],
                          const SizedBox(height: 24),
                          // Precio
                          if (_selectedVariant != null) ...[
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text(
                                  'Precio:',
                                  style: TextStyle(
                                    fontSize: 16,
                                    color: AppColors.grey,
                                  ),
                                ),
                                Text(
                                  'Bs ${_selectedVariant!.precio.toStringAsFixed(2)}',
                                  style: const TextStyle(
                                    fontSize: 24,
                                    fontWeight: FontWeight.bold,
                                    color: AppColors.accent,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Text(
                              _selectedVariant!.cantidad > 0
                                  ? '${_selectedVariant!.cantidad} unidades disponibles'
                                  : 'Agotado',
                              style: TextStyle(
                                color: _selectedVariant!.cantidad > 0
                                    ? AppColors.success
                                    : AppColors.danger,
                              ),
                            ),
                            const SizedBox(height: 16),
                            ElevatedButton(
                              onPressed: _selectedVariant!.cantidad > 0
                                  ? () {
                                      // TODO: Implementar carrito en Ciclo 2
                                    }
                                  : null,
                              style: ElevatedButton.styleFrom(
                                minimumSize: const Size(double.infinity, 50),
                              ),
                              child: const Text('Agregar al Carrito'),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ],
                ),
              ),
      ),
    );
  }

  Widget _buildInfoChip(IconData icon, String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: AppColors.greyLight,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: AppColors.grey),
          const SizedBox(width: 4),
          Text(
            text,
            style: const TextStyle(
              fontSize: 12,
              color: AppColors.dark,
            ),
          ),
        ],
      ),
    );
  }
}          