from django.contrib import messages
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpRequest, HttpResponse

from .forms import CommentForm
from .models import Category, Comment, Product


def product_list(request: HttpRequest, category_slug: str=None):
    """
            Returns the available categories and products
    
            Parameters:
                request(HttpRequest):The type of request performed on the product details (eg: GET, POST...)
                category_slug(slug): The category slug the product belongs to
    
            Returns:
                response(HttpResponse): an HTTPResponse filled with the HTTPRequest type, the template name and a content object to be processed and displayed on the products.html page containing the categories and products.
    """
    categories = Category.objects.all()
    products = Product.objects.select_related("category").annotate(
        avg_rating=Avg("comments__rating"), total_ratings=Count("comments")
    )
    if category_slug:
        products = products.filter(category__slug=category_slug)
    return render(request, "products.html", {"categories": categories, "products": products})


def product_detail(request: HttpRequest, category_slug: str, pk: int):
    """
        Returns the details of a product, including category, product description, image, tags and related user comments and ratings

        Parameters:
            request(HttpRequest):The type of request performed on the product details (eg: GET, POST...)
            category_slug(str): The category slug the product belongs to
            pk(int): The primary key associated with the product

        Returns:
            response(HttpResponse): an HTTPResponse filled with the HTTPRequest type, the template name and a content object to be processed and displayed on the product.html page containing the product details, tags, related products, user comments and ratings, request type and form information.
    """
    product = get_object_or_404(
        Product.objects.select_related("category").annotate(
            avg_rating=Avg("comments__rating"), total_ratings=Count("comments")
        ),
        pk=pk,
        category__slug=category_slug,
    )

    related_products = (
        Product.objects.filter(category=product.category)
        .exclude(pk=product.pk)
        .annotate(avg_rating=Avg("comments__rating"), total_ratings=Count("comments"))
        .order_by("-avg_rating", "-total_ratings", "name")[:8]
    )

    # get associated product tags ordered by name
    tags = product.tag.order_by("name")

    comments = product.comments.select_related("user").order_by("-created_at")

    if request.method == "POST":
        form = CommentForm(request.POST, initial={"user": request.user if request.user.is_authenticated else None})
        if form.is_valid():
            rating = form.cleaned_data["rating"]
            text = form.cleaned_data.get("text", "")

            if request.user.is_authenticated:
                # Upsert: update existing comment or create a new one
                comment, created = Comment.objects.get_or_create(
                    product=product, user=request.user, defaults={"rating": rating, "text": text}
                )
                if not created:
                    comment.rating = rating
                    comment.text = text
                    comment.save()
                messages.success(request, "Your rating was {}.".format("submitted" if created else "updated"))
            else:
                # Guest: create a new comment (no uniqueness constraint)
                comment = form.save(commit=False)
                comment.product = product
                comment.save()
                messages.success(request, "Thank you for your rating.")

            return redirect("product_detail", category_slug=category_slug, pk=product.pk)
    else:
        # Clear the form after comment and rating submssion
        initial = {}
        form = CommentForm(initial=initial) 

    return render(
        request,
        "product.html",
        {"product": product, "tags": tags, "comments": comments, "related_products": related_products, "form": form},
    )
