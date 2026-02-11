from extras.validators import CustomValidator


class VMValidator(CustomValidator):
    def validate(self, instance, request):
        # Rol and cluster are required
        if not instance.role:
            self.fail('Role is required', field='role')
        if not instance.cluster:
            self.fail('Cluster is required', field='cluster')

        # If role is Odoo, validate tags and assign resources
        if instance.role.slug == 'odoo':
            # Obtain VM tags from request (includes unsaved changes from the form)
            vm_tags = []
            if request and hasattr(request, 'POST') and 'tags' in request.POST:
                from extras.models import Tag
                tag_ids = request.POST.getlist('tags')
                if tag_ids:  # Only query if there are tag IDs
                    tags = Tag.objects.filter(id__in=tag_ids)
                    vm_tags = [tag.slug for tag in tags]
            elif instance.pk:  # Only access tags if instance has been saved (has primary key)
                # Fallback to existing tags
                vm_tags = [tag.slug for tag in instance.tags.all()]

            # Valid odoo tags
            odoo_tags = ['odoo-s', 'odoo-m', 'odoo-l']

            # Find odoo tags in VM
            found_odoo_tags = [tag for tag in vm_tags if tag in odoo_tags]

            # Must have exactly one
            if len(found_odoo_tags) == 0:
                self.fail('VMs with role "odoo" must have exactly one of this tags: odoo-s, odoo-m, or odoo-l', field='tags')
            elif len(found_odoo_tags) > 1:
                self.fail('VMs with role "odoo" must have only ONE tag: odoo-s, odoo-m, or odoo-l', field='tags')

            # Configuration according to tag
            tag_configs = {
                'odoo-s': {'vcpus': 1, 'memory': 2000, 'disk': 30000},
                'odoo-m': {'vcpus': 2, 'memory': 4000, 'disk': 50000},
                'odoo-l': {'vcpus': 4, 'memory': 8000, 'disk': 60000},
            }

            # Assign resources according to tag
            odoo_tag = found_odoo_tags[0]
            config = tag_configs[odoo_tag]

            instance.vcpus = config['vcpus']
            instance.memory = config['memory']
            instance.disk = config['disk']
