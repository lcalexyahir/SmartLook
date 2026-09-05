import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/models/product_model.dart';
import '../../../core/network/api_client.dart';
import '../../../shared/theme/app_colors.dart';
import '../../../shared/widgets/loading_overlay.dart';
import '../../../shared/widgets/product_card.dart';
import '../../../shared/widgets/empty_state.dart';
import '../data/repositories/catalog_repository_impl.dart';
import '../data/sources/catalog_remote_source.dart';
import 'product_detail_screen.dart';

class ProductListScreen extends StatefulWidget {
  const ProductListScreen({super.key});

  @override
  State<ProductListScreen> createState() => _ProductListScreenState();
}

class _ProductListScreenState extends State<ProductListScreen> {
  late final CatalogRepositoryImpl _catalogRepository;
  List<Product> _products = [];
  List<dynamic> _categories = [];
  List<dynamic> _brands = [];
  List<dynamic> _sizes = [];
  List<dynamic> _colors = [];
  bool _isLoading = false;
  String? _selectedCategory;
  String? _selectedBrand;
  String? _selectedSize;
  String? _selectedColor;
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    final apiClient = context.read<ApiClient>();
    _catalogRepository = CatalogRepositoryImpl(
      remoteSource: CatalogRemoteSource(apiClient: apiClient),
    );
    _loadFilters();
    _loadProducts();
  }

  Future<void> _loadFilters() async {
    try {
      final categories = await _catalogRepository.getCategories();
      final brands = await _catalogRepository.getBrands();
      final sizes = await _catalogRepository.getSizes();
      final colors = await _catalogRepository.getColors();

      if (mounted) {
        setState(() {
          _categories = categories;
          _brands = brands;
          _sizes = sizes;
          _colors = colors;
        });
      }
    } catch (e) {
      // Silenciosamente falla si no hay filtros
    }
  }

  Future<void> _loadProducts() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final products = await _catalogRepository.getProducts(
        categoria: _selectedCategory,
        marca: _selectedBrand,
        talla: _selectedSize,
        color: _selectedColor,
        busqueda: _searchQuery,
      );

      if (mounted) {
        setState(() {
          _products = products
              .map((entity) => entity.toModel())
              .toList();
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _products = [];
          _isLoading = false;
        });
      }
    }
  }

  void _showFilterSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) {
        return Container(
          padding: const EdgeInsets.all(24),
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'Filtros',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String?>(
                value: _selectedCategory,
                decoration: const InputDecoration(labelText: 'Categoría'),
                items: [
                  const DropdownMenuItem<String?>(
                    value: null,
                    child: Text('Todas'),
                  ),
                  ..._categories.map<DropdownMenuItem<String?>>((cat) {
                    return DropdownMenuItem<String?>(
                      value: cat['nombre'],
                      child: Text(cat['nombre']),
                    );
                  }),
                ],
                onChanged: (value) {
                  setState(() {
                    _selectedCategory = value;
                  });
                },
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String?>(
                value: _selectedBrand,
                decoration: const InputDecoration(labelText: 'Marca'),
                items: [
                  const DropdownMenuItem<String?>(
                    value: null,
                    child: Text('Todas'),
                  ),
                  ..._brands.map<DropdownMenuItem<String?>>((brand) {
                    return DropdownMenuItem<String?>(
                      value: brand['nombre'],
                      child: Text(brand['nombre']),
                    );
                  }),
                ],
                onChanged: (value) {
                  setState(() {
                    _selectedBrand = value;
                  });
                },
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String?>(
                value: _selectedSize,
                decoration: const InputDecoration(labelText: 'Talla'),
                items: [
                  const DropdownMenuItem<String?>(
                    value: null,
                    child: Text('Todas'),
                  ),
                  ..._sizes.map<DropdownMenuItem<String?>>((size) {
                    return DropdownMenuItem<String?>(
                      value: size['nombre'],
                      child: Text(size['nombre']),
                    );
                  }),
                ],
                onChanged: (value) {
                  setState(() {
                    _selectedSize = value;
                  });
                },
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String?>(
                value: _selectedColor,
                decoration: const InputDecoration(labelText: 'Color'),
                items: [
                  const DropdownMenuItem<String?>(
                    value: null,
                    child: Text('Todos'),
                  ),
                  ..._colors.map<DropdownMenuItem<String?>>((color) {
                    return DropdownMenuItem<String?>(
                      value: color['nombre'],
                      child: Text(color['nombre']),
                    );
                  }),
                ],
                onChanged: (value) {
                  setState(() {
                    _selectedColor = value;
                  });
                },
              ),
              const SizedBox(height: 24),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () {
                        setState(() {
                          _selectedCategory = null;
                          _selectedBrand = null;
                          _selectedSize = null;
                          _selectedColor = null;
                        });
                        Navigator.pop(context);
                        _loadProducts();
                      },
                      child: const Text('Limpiar'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: ElevatedButton(
                      onPressed: () {
                        Navigator.pop(context);
                        _loadProducts();
                      },
                      child: const Text('Aplicar'),
                    ),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('SmartLook'),
        actions: [
          IconButton(
            icon: const Icon(Icons.filter_list),
            onPressed: _showFilterSheet,
          ),
        ],
      ),
      body: LoadingOverlay(
        isLoading: _isLoading,
        message: 'Cargando productos...',
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.all(16),
              child: TextField(
                decoration: InputDecoration(
                  hintText: 'Buscar producto...',
                  prefixIcon: const Icon(Icons.search),
                  suffixIcon: _searchQuery.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.clear),
                          onPressed: () {
                            setState(() {
                              _searchQuery = '';
                            });
                            _loadProducts();
                          },
                        )
                      : null,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                onChanged: (value) {
                  setState(() {
                    _searchQuery = value;
                  });
                },
                onSubmitted: (_) => _loadProducts(),
              ),
            ),
            Expanded(
              child: _products.isEmpty && !_isLoading
                  ? const EmptyState(
                      icon: Icons.shopping_bag,
                      title: 'No hay productos',
                      subtitle: 'No se encontraron productos con los filtros seleccionados',
                    )
                  : GridView.builder(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 2,
                        childAspectRatio: 0.65,
                        crossAxisSpacing: 12,
                        mainAxisSpacing: 12,
                      ),
                      itemCount: _products.length,
                      itemBuilder: (context, index) {
                        final product = _products[index];
                        return ProductCard(
                          product: product,
                          onTap: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (context) => ProductDetailScreen(
                                  productId: product.idProducto,
                                ),
                              ),
                            );
                          },
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
}